"""
YouTube 영상 수집 및 필터링 메인 스크립트
"""
import logging
import sys
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 프로젝트 루트 경로 설정
PROJECT_ROOT = str(Path(__file__).parent.parent)
os.environ['PROJECT_ROOT'] = PROJECT_ROOT

# .env 파일 로드
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# OPENAI_API_KEY 확인
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다")

# 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_pipeline.models import VideoStatus, init_db, get_session, video_exists_in_db, save_video
from data_pipeline.youtube import (
    extract_video_urls,
    download_video_data,
    clean_subtitles,
    is_text_valid,
    filter_and_refine_title
)

# 로깅 설정
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'youtube_pipeline.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# YouTube 채널 설정
YOUTUBE_CHANNELS = [
    # 테스트용 URL (실제 채널 추가)
    "https://www.youtube.com/@muchelin1/videos",
]


def process_video(
    url: str,
    session,
    llm: ChatOpenAI
) -> bool:
    """
    단일 영상 처리

    Returns:
        True if successfully processed/stored, False otherwise
    """
    logger.info(f"🔍 처리 중: {url}")

    # 1. 데이터 수집
    video_data = download_video_data(url)
    if not video_data:
        logger.warning(f"1. ⚠️ 데이터 수집 실패: {url}")
        return False

    video_id = video_data["video_id"]
    logger.info(f"   제목: {video_data['title']}")
    logger.info(f"   URL: {video_data['url']}")

    # 2. 중복 필터링 (DB ID 확인)
    if video_exists_in_db(session, video_id):
        logger.info(f"2. 🔁 이미 존재하는 영상: {video_id}")
        return False

    # 3. 자막 확인
    if not video_data["has_subtitles"]:
        logger.warning(f"3. 📝 자막 없음: {video_id}")
        save_video(session, video_id, video_data, VideoStatus.NO_SUBTITLE)
        return False

    # 4. 자막 정제
    cleaned_subtitles = clean_subtitles(video_data["subtitles"])
    if not is_text_valid(cleaned_subtitles):
        logger.warning(f"4. ❌ 정제된 텍스트 부족: {video_id}")
        save_video(session, video_id, video_data, VideoStatus.NO_SUBTITLE)
        return False

    # 5. LLM 필터링 + 제목 개선
    logger.info(f"🤖 LLM 필터링 중: {video_id}")
    llm_result = filter_and_refine_title(
        title=video_data["title"],
        llm=llm,
        description=video_data.get("description")
    )

    if not llm_result:
        logger.error(f"❌ LLM 필터링 실패: {video_id}")
        save_video(session, video_id, video_data, VideoStatus.LLM_FILTER_FAILED)
        return False

    # 6. LLM 판단 확인
    if not llm_result["is_relevant"]:
        logger.info(f"6. ❌ 불필요한 콘텐츠: {llm_result['reason']}")
        save_video(session, video_id, video_data, VideoStatus.UNNECESSARY, reason=llm_result['reason'])
        return False
    
    # llm_result = {
    # "is_relevant": True,
    # "reason": "reason",
    # "refined_title": "refined_title"}

    # 7. DB 저장 (CLEANSED 상태)
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


def main():
    """메인 처리 함수"""
    logger.info("=" * 60)
    logger.info("🚀 YouTube 데이터 수집 시작")
    logger.info("=" * 60)

    # DB 초기화
    init_db()
    session = get_session()

    # LLM 초기화
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    stats = {
        "total": 0,
        "processed": 0,
        "skipped": 0,
        "failed": 0
    }

    try:
        # 채널 순회
        for channel_url in YOUTUBE_CHANNELS:
            logger.info(f"\n📺 채널 처리: {channel_url}")

            # 1단계: 채널에서 영상 URL 추출 (3년 이내만)
            video_urls = extract_video_urls(channel_url)
            if not video_urls:
                logger.warning(f"⚠️ 처리할 영상이 없습니다: {channel_url}")
                continue

            # 2단계: 각 영상 처리
            for video_url in video_urls:
                stats["total"] += 1
                try:
                    if process_video(video_url, session, llm):
                        stats["processed"] += 1
                    else:
                        stats["skipped"] += 1
                except Exception as e:
                    logger.error(f"❌ 예외 발생: {str(e)}")
                    stats["failed"] += 1

    except KeyboardInterrupt:
        logger.info("\n⚠️ 사용자가 중단함")
    except Exception as e:
        logger.error(f"❌ 치명적 오류: {str(e)}", exc_info=True)
    finally:
        session.close()

    # 통계 출력
    logger.info("\n" + "=" * 60)
    logger.info("📊 처리 완료")
    logger.info(f"   총계: {stats['total']}")
    logger.info(f"   성공: {stats['processed']}")
    logger.info(f"   스킵: {stats['skipped']}")
    logger.info(f"   실패: {stats['failed']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
