"""
설정 관리 모듈
"""
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', Path(__file__).parent.parent))
load_dotenv(dotenv_path=str(PROJECT_ROOT / ".env"))

class Config:
    """애플리케이션 설정"""

    # 데이터 경로 (절대경로)
    DATA_DIR = str(PROJECT_ROOT / "data" / "papers")
    CHROMA_DB_PATH = str(PROJECT_ROOT / "chroma_db")

    # 문서 처리 설정
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 150 # 나뉘어지는, 겹쳐지는 부분을 의미하는듯

    # 임베딩 설정
    EMBEDDING_MODEL = "intfloat/multilingual-e5-large" #"all-MiniLM-L6-v2"

    # LLM 설정
    LLM_MODEL = "gpt-4o-mini"
    LLM_TEMPERATURE = 0.3
    OPENAI_API_KEY = os.environ["OPEN_API_KEY"]

    # 비전(Vision) 설정
    IMAGE_DETAIL = "low"  # "low" 또는 "high"

    # RAG 설정
    TOP_K = 3

    @classmethod
    def validate(cls):
        """설정 검증"""
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR, exist_ok=True)
            print(f"📁 {cls.DATA_DIR} 디렉토리 생성됨")

    @classmethod
    def print_config(cls):
        """현재 설정 출력"""
        print("\n⚙️  현재 설정:")
        print(f"   데이터 폴더: {cls.DATA_DIR}")
        print(f"   벡터 DB: {cls.CHROMA_DB_PATH}")
        print(f"   청크 크기: {cls.CHUNK_SIZE} 토큰")
        print(f"   임베딩 모델: {cls.EMBEDDING_MODEL}")
        print(f"   LLM: {cls.LLM_MODEL}")
        print(f"   이미지 퀄리티: {cls.IMAGE_DETAIL}")
        print(f"   검색 결과 수: {cls.TOP_K}개")
        print(f"   openai 키(4): {cls.OPENAI_API_KEY[:3]}")

