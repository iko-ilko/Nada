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
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MIN_CHUNK_SIZE = 240

    # 임베딩 설정
    EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
    NORMALIZE_EMBEDDINGS = True

    # LLM 설정
    LLM_MODEL = "gpt-4o-mini"
    MAKE_QUERY_TEMPERATURE = 0.0
    ANALYSIS_TEMPERATURE = 0.7
    OPENAI_API_KEY = os.environ["OPEN_API_KEY"]
    if LLM_MODEL == "gpt-5-mini": # 후에 모델별 설정으로 바꾸기. 기본값 0.0 0.7 두고.
        MAKE_QUERY_TEMPERATURE = 1
        ANALYSIS_TEMPERATURE = 1

    # 비전(Vision) 설정
    IMAGE_DETAIL = "low"

    # RAG 설정
    TOP_K = 7
    RRF_K = 60 # Dense + BM25 두 방식의 결과를 병합하는 k값. 불규칙한 변동성을 줄여서 패턴이나 추세를 더 명확하게 스무딩 처리하는 파라미터로 이해. 민감도 조절.

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
