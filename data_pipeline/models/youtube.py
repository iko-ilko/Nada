"""
YouTube 비디오 데이터 모델
"""
import os
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# 데이터베이스 경로
DEFAULT_DB_PATH = os.path.join(os.environ['PROJECT_ROOT'], "youtube_data.db")


class VideoStatus(str, Enum):
    """비디오 처리 상태"""
    NO_SUBTITLE = "no_subtitle"
    LLM_FILTER_FAILED = "llm_filter_failed"
    UNNECESSARY = "unnecessary"
    CLEANSED = "cleansed"
    CHUNKED = "chunked"
    YT_RATE_LIMIT = "yt_rate_limit"  # yt-dlp 429 에러 - 나중에 재시도


class YouTubeVideo(Base):
    """YouTube 비디오 정보"""
    __tablename__ = "youtube_videos"

    id = Column(String, primary_key=True, index=True)  # YouTube video_id
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    title_refined = Column(String, nullable=True)
    subtitles = Column(Text, nullable=True)  # 정제된 자막 텍스트
    reason = Column(Text, nullable=True)  # LLM 판단 근거
    uploaded_at = Column(DateTime, nullable=False)  # UTC
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default=VideoStatus.NO_SUBTITLE, index=True)

    def __repr__(self):
        return f"<YouTubeVideo(id={self.id}, title={self.title}, status={self.status})>"


# 글로벌 engine (싱글톤)
_engine = None
_SessionLocal = None


def init_db():
    """데이터베이스 초기화"""
    global _engine, _SessionLocal

    db_path = DEFAULT_DB_PATH

    _engine = create_engine(f"sqlite:///{db_path}")
    _SessionLocal = sessionmaker(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    return _engine


def get_session():
    """세션 반환 (init_db 호출 필수)"""
    global _SessionLocal

    if _SessionLocal is None:
        raise RuntimeError("init_db()를 먼저 호출해야 합니다")

    return _SessionLocal()


def video_exists_in_db(session, video_id: str) -> bool:
    """
    DB에 이미 존재하는 영상인지 확인

    Args:
        session: SQLAlchemy 세션
        video_id: YouTube 비디오 ID

    Returns:
        존재 여부
    """
    return session.query(YouTubeVideo).filter_by(id=video_id).first() is not None


def save_video(
    session,
    video_id: str,
    video_data: dict,
    status: VideoStatus,
    title_refined: str = None,
    subtitles: str = None,
    reason: str = None
) -> bool:
    """
    YouTube 영상 정보를 DB에 저장

    Args:
        session: SQLAlchemy 세션
        video_id: YouTube 비디오 ID
        video_data: download_video_data()에서 반환한 데이터
        status: 저장할 상태
        title_refined: 개선된 제목 (선택)
        subtitles: 정제된 자막 (선택)
        reason: LLM 판단 근거 (선택)

    Returns:
        저장 성공 여부
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        video = YouTubeVideo(
            id=video_id,
            url=video_data["url"],
            title=video_data["title"],
            title_refined=title_refined,
            subtitles=subtitles,
            reason=reason,
            uploaded_at=video_data["uploaded_at"],
            status=status
        )
        session.add(video)
        session.commit()
        return True

    except Exception as e:
        logger.error(f"❌ DB 저장 실패 ({video_id}): {str(e)}")
        session.rollback()
        return False
