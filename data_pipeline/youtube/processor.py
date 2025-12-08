"""
YouTube 영상 처리 파이프라인
"""
import re
import logging
from typing import Optional
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI

from data_pipeline.models import VideoStatus, video_exists_in_db, save_video
from data_pipeline.youtube.downloader import download_video_data, generate_url
from data_pipeline.youtube.filter import filter_and_refine_title

logger = logging.getLogger(__name__)


def clean_subtitles(subtitle_text: str) -> str:
    """
    VTT/자막 텍스트 정제

    Args:
        subtitle_text: 원본 자막 텍스트 (VTT 포맷)

    Returns:
        정제된 텍스트
    """
    if not subtitle_text:
        return ""

    paragraphs = []

    for line in subtitle_text.split('\n'):
        line = line.strip()

        if line.startswith(('Kind:', 'Language:', 'WEBVTT', 'NOTE')) or not line.strip(): # 양쪽 끝에 공백이 없다고 가정(그래보임)하고 제거된 라인 할당 x. 
            continue

        if '-->' in line or re.search(r'<\d{2}:\d{2}:', line):
            continue

        line = line.replace('&gt;', '').replace('[음악]', '').replace('네.', '').replace('안녕하세요.', '')
        
        # 중복 제거
        if paragraphs and line == paragraphs[-1]:
            continue

        paragraphs.append(line)

    # 모든 텍스트를 공백으로 연결
    result = ' '.join(paragraphs)

    # 마침표, 물음표, 느낌표 기준으로 개행
    result = re.sub(r'([\.!?])\s+', r'\1\n', result)

    return result.strip()


def is_text_valid(text: str, min_length: int = 100) -> bool:
    """
    정제된 텍스트 유효성 검사

    Args:
        text: 정제된 텍스트
        min_length: 최소 길이

    Returns:
        유효 여부
    """
    if not text or len(text) < min_length:
        logger.warning(f"⚠️ 텍스트 길이 부족: {len(text)} < {min_length}")
        return False

    return True


def process_video(
    video_id: str,
    session,
    llm: ChatOpenAI
) -> bool:
    """
    단일 영상 처리

    Args:
        video_id: YouTube 비디오 ID
        session: SQLAlchemy 세션
        llm: ChatOpenAI 인스턴스

    Returns:
        True if successfully processed/stored, False otherwise
    """
    try:
        # 1. URL 생성
        url = generate_url(video_id)

        # 2. 중복 필터링
        if video_exists_in_db(session, video_id):
            logger.info(f"2. 🔁 이미 존재하는 영상: {video_id}")
            return False

        # 3. 데이터 수집
        video_data = download_video_data(url)
        if not video_data:
            logger.warning(f"3. ⚠️ 데이터 수집 실패: {video_id}")
            return False

        logger.info(f"   제목: {video_data['title']}")
        logger.info(f"   URL: {video_data['url']}")

        # 4. 자막 확인
        if not video_data["has_subtitles"]:
            logger.warning(f"4. 📝 자막 없음: {video_id}")
            save_video(session, video_id, video_data, VideoStatus.NO_SUBTITLE)
            return False

        # 5. 자막 정제
        cleaned_subtitles = clean_subtitles(video_data["subtitles"])
        if not is_text_valid(cleaned_subtitles):
            logger.warning(f"5. ❌ 정제된 텍스트 부족: {video_id}")
            save_video(session, video_id, video_data, VideoStatus.NO_SUBTITLE)
            return False

        # 6. LLM 필터링 + 제목 개선
        llm_result = filter_and_refine_title(
            title=video_data["title"],
            llm=llm,
            description=video_data.get("description")
        )
        logger.info(f"    바뀐 제목: {llm_result['refined_title']}")

        if not llm_result:
            logger.error(f"6. ❌ LLM 필터링 실패: {video_id}")
            save_video(session, video_id, video_data, VideoStatus.LLM_FILTER_FAILED)
            return False

        # 7. LLM 판단 확인
        if not llm_result["is_relevant"]:
            logger.info(f"7. ❌ 불필요한 콘텐츠: {llm_result['reason']}")
            save_video(session, video_id, video_data, VideoStatus.UNNECESSARY, reason=llm_result['reason'])
            return False

        # 8. DB 저장 (CLEANSED 상태)
        refined_title = llm_result.get("refined_title") or video_data["title"]
        logger.info(f"✅ 저장 완료")

        save_video(
            session,
            video_id,
            video_data,
            VideoStatus.CLEANSED,
            title_refined=refined_title,
            subtitles=cleaned_subtitles,
            reason=llm_result['reason']
        )

        return True

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            logger.warning(f"⏸️ YouTube 속도 제한 (나중에 재시도): {error_msg}")
            save_video(
                session,
                video_id,
                {
                    "url": generate_url(video_id),
                    "title": "Unknown",
                    "uploaded_at": datetime.now(timezone.utc)
                },
                VideoStatus.YT_RATE_LIMIT
            )
            raise
        else:
            logger.error(f"❌ 예외 발생 ({video_id}): {error_msg}")
            raise
