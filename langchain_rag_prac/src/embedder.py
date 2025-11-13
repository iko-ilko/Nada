"""
임베딩 모듈
문서를 벡터로 변환합니다.
"""
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import Config


class EmbeddingManager:
    """임베딩 관리자"""

    def __init__(self, model_name=None):
        self.model_name = model_name or Config.EMBEDDING_MODEL
        self.embeddings = None

    def get_embeddings(self):
        """
        임베딩 모델 로드 (처음 로드시만 다운로드)
        """
        if self.embeddings is not None:
            return self.embeddings

        print(f"\n🔄 임베딩 모델 로드 중...")
        print(f"   모델: {self.model_name}")
        print(f"   (처음 실행시 다운로드될 수 있습니다)")

        self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)

        print(f"✅ 임베딩 모델 준비 완료")
        return self.embeddings
