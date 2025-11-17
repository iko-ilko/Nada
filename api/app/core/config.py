"""
설정 관리 모듈
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', Path(__file__).parent.parent.parent))
load_dotenv(dotenv_path=str(PROJECT_ROOT / ".env"))

class Config:
    """애플리케이션 설정"""

    # 데이터 경로 (절대경로)
    DATA_DIR = str(PROJECT_ROOT / "data" / "papers")
    CHROMA_DB_PATH = str(PROJECT_ROOT / "chroma_db")
    LOGS_DIR = str(PROJECT_ROOT / "logs")

    # 문서 처리 설정
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 150
    MIN_CHUNK_SIZE = 240

    # 임베딩 설정
    EMBEDDING_MODEL = "intfloat/multilingual-e5-large"

    # LLM 설정
    LLM_MODEL = "gpt-4o-mini"
    LLM_TEMPERATURE = 0.7
    OPENAI_API_KEY = os.environ["OPEN_API_KEY"]

    # 비전(Vision) 설정
    IMAGE_DETAIL = "low"

    # RAG 설정
    TOP_K = 3

    # Cloudinary 설정
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")
    CLOUDINARY_IMAGE_PATH = "Nada/users"
    CLOUDINARY_EXPIRE_MINUTES = 5  # 인증 이미지 접근 만료 시간 (분)

    @classmethod
    def validate(cls):
        """설정 검증"""
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR, exist_ok=True)
            logger.info(f"📁 {cls.DATA_DIR} 디렉토리 생성됨")

    @classmethod
    def print_config(cls):
        """현재 설정 출력"""
        logger.info("⚙️  현재 설정:")
        logger.info(f"   데이터 폴더: {cls.DATA_DIR}")
        logger.info(f"   벡터 DB: {cls.CHROMA_DB_PATH}")
        logger.info(f"   청크 크기: {cls.CHUNK_SIZE}")
        logger.info(f"   임베딩 모델: {cls.EMBEDDING_MODEL}")
        logger.info(f"   LLM: {cls.LLM_MODEL}")
        logger.info(f"   검색 결과 수: {cls.TOP_K}개")
