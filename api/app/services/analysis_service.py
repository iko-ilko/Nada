"""
분석 서비스
"""
import os
import logging
from pathlib import Path
from app.core.config import Config
from app.core.indexer import EmbeddingManager, VectorStoreManager
from app.core.llm import get_llm
from app.core.rag import build_analysis_chain
from app.core.vision import extract_json
from app.core.chain_logger import ChainLogger
from app.schemas.request import AnalysisRequest
from app.schemas.response import AnalysisResponse
from app.utils import cloudinary

logger = logging.getLogger(__name__)


class AnalysisService:
    """분석 서비스"""

    def __init__(self):
        """서비스 초기화"""
        self.embedding_manager = EmbeddingManager()
        self.embeddings = self.embedding_manager.get_embeddings()

        self.db_manager = VectorStoreManager(self.embeddings)
        try:
            self.db_manager.load_vectorstore()
        except Exception as e:
            raise RuntimeError(f"벡터 DB를 로드할 수 없습니다: {e}")

        self.llm = get_llm()
        self.system_prompt = self._load_prompt()
        self.logger = ChainLogger()

    def _load_prompt(self) -> str:
        """시스템 프롬프트 로드"""
        project_root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
        prompt_path = project_root / "app/core/prompt/response_ko.prt"
        return prompt_path.read_text(encoding="utf-8")

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        분석 실행

        Args:
            request: AnalysisRequest

        Returns:
            AnalysisResponse
        """
        try:
            # 1. 이미지 파일을 Cloudinary에 인증 업로드
            logger.info("📤 이미지를 Cloudinary에 업로드 중...")
            image_data = request.image_file.file.read()
            upload_result = cloudinary.upload_authenticated_image(
                image_data=image_data,
                expire_minutes=Config.CLOUDINARY_EXPIRE_MINUTES
            )
            image_url = upload_result["secure_url"]
            logger.info(f"✅ 이미지 업로드 완료: {image_url}")

            # 2. 체인 구성
            retriever = self.db_manager.get_retriever()
            chain = build_analysis_chain(
                retriever=retriever,
                llm=self.llm,
                system_prompt=self.system_prompt,
                user_state=request.user_state,
                image_url=image_url,
                image_detail=Config.IMAGE_DETAIL,
            )

            # 3. 체인 실행
            raw_response = chain.invoke(request.user_state)

            # 4. JSON 추출
            analysis = extract_json(raw_response)

            # 5. 검색 결과 (유사도 포함) - 로깅용
            search_results_with_score = self.db_manager.vectorstore.similarity_search_with_score(
                request.user_state,
                k=Config.TOP_K
            )
            search_results = [doc for doc, score in search_results_with_score]
            search_scores = [score for doc, score in search_results_with_score]

            # 6. 로그 저장
            log_path = self.logger.save_analysis(
                image_url=image_url,
                user_state=request.user_state,
                search_results=search_results,
                analysis=analysis,
                image_detail=Config.IMAGE_DETAIL,
                model=Config.LLM_MODEL,
                search_scores=search_scores,
            )

            return AnalysisResponse(
                status="success",
                analysis=analysis
            )

        except Exception as e:
            logger.exception(f"❌ 분석 중 에러 발생")
            return AnalysisResponse(
                status="error",
                analysis={},
                error=str(e),
            )


# 싱글톤 인스턴스
_service = None


def get_analysis_service() -> AnalysisService:
    """분석 서비스 인스턴스 반환"""
    global _service
    if _service is None:
        _service = AnalysisService()
    return _service
