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

from data_pipeline.models import init_db, get_session
from data_pipeline.youtube import (
    extract_video_urls,
    process_video
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
    # "https://www.youtube.com/@muchelin1/videos", # 남자 헤어
    # "https://www.youtube.com/@lamuqe_magicup/videos", # 여자 뷰티
    # "https://www.youtube.com/@una_only/videos" #여자 뷰티(윤곽 피부) # 삭제하고 429 하나 있음. 왜 계속 429가 뜨지? -> 자막 서버는 별도의 서버라 엄격 할 수도있다는 의견.
    "https://www.youtube.com/@krtiger/videos" #윤곽 # 429, 자막없음 영상 많음 -> eng로 번역 또는 stt
]


def get_video_id_from_url(url: str):
    """
    YouTube URL에서 video_id 추출

    Args:
        url: YouTube 영상 URL

    Returns:
        video_id 또는 None
    """
    try:
        # https://www.youtube.com/watch?v=XXXXXXXXXX
        return url.split('v=')[1].split('&')[0]
    except Exception:
        return None


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
                video_id = get_video_id_from_url(video_url)
                if not video_id:
                    logger.warning(f"🔍 처리 시작 {stats['total']}/{len(video_urls)}: ⚠️ 유효하지 않은 URL")
                    stats["skipped"] += 1
                    continue

                logger.info(f"🔍 처리 시작 {stats['total']}/{len(video_urls)}: {video_id}")
                try:
                    if process_video(video_id, session, llm):
                        stats["processed"] += 1
                    else:
                        stats["skipped"] += 1
                except Exception as e:
                    logger.error(f"❌ 예외 발생 ({video_id}): {str(e)}")
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
