"""
분석 서비스
"""
import os
import logging
from pathlib import Path
from app.core.config import Config
from app.core.indexer import EmbeddingManager, VectorStoreManager
from app.core.llm import get_llm
from app.core.vision import extract_json
from app.core.chain_logger import ChainLogger
from app.core import rag
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
        self.analysis_prompt = self._load_prompt("analysis_ko.prt")
        self.make_query_prompt = self._load_prompt("make_query_ko.prt")
        self.logger = ChainLogger()

        # BM25용 문서 로드 (초기화 시 1회)
        self.bm25_retriever = None

    def _load_prompt(self, name) -> str:
        """시스템 프롬프트 로드"""
        project_root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
        prompt_path = project_root / f"app/core/prompt/{name}"
        return prompt_path.read_text(encoding="utf-8")

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        분석 실행 (최적화된 MultiQuery 방식)

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

            # 2. 이미지 분석 + 3개 검색 쿼리 생성 (1회 API 호출)
            logger.info("🔍 이미지 분석 및 검색 쿼리 생성 중...")
            from app.core.vision import analyze_image_and_create_multi_queries

            import base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')

            result = analyze_image_and_create_multi_queries(
                vision_llm=self.llm,
                image_base64=image_base64,
                user_query=request.user_state,
                make_query_prompt=self.make_query_prompt
            )
            image_analysis = result["image_analysis"]
            search_queries = result["search_queries"]
            make_query_tokens = result.get("total_tokens", 0)
            logger.info(f"✅ {len(search_queries)}개 검색 쿼리 생성 완료")

            # 3. BM25 리트리버 초기화 (필요시)
            if self.bm25_retriever is None:
                self.bm25_retriever = rag.initialize_bm25_retriever(self.db_manager)

            # 4. 하이브리드 검색 (4개 쿼리로 8회 검색: Dense k=5 + BM25 k=5)
            logger.info(f"🔍 하이브리드 검색 시작... ({len(search_queries)}개 쿼리)")
            search_results, rrf_scores, search_metadata, detailed_search_logs = rag.perform_hybrid_search(
                self.db_manager,
                self.bm25_retriever,
                search_queries
            )
            logger.info(f"   ✓ 최종 결과: {len(search_results)}개 문서 (Top {Config.TOP_K})")

            # 5. LLM 최종 분석 실행
            logger.info("🤖 LLM 분석 중...")
            from app.core.vision import format_docs, create_multimodal_message

            formatted_docs = format_docs(search_results)
            messages = create_multimodal_message({
                "formatted_docs": formatted_docs,
                "user_state": request.user_state,
                "image_url": image_url,
                "detail": Config.IMAGE_DETAIL,
                "analysis_prompt": self.analysis_prompt,
            })

            raw_response = self.llm.invoke(messages)
            analysis = extract_json(raw_response.content)

            # 최종 분석 토큰 정보 추출
            analysis_tokens = 0
            if hasattr(raw_response, 'response_metadata'):
                usage = raw_response.response_metadata.get('token_usage', {})
                analysis_tokens = usage.get('total_tokens', 0)

            logger.info(f"✅ 분석 완료")

            # 6. 참고문헌 추출
            references = [doc.metadata.get("source", f"doc_{i}") for i, doc in enumerate(search_results)]

            # 7. 로그 저장
            llm_raw_response = {
                "image_analysis": image_analysis,
                "search_queries": search_queries
            }

            log_path = self.logger.save_analysis(
                image_url=image_url,
                user_state=request.user_state,
                search_results=search_results,
                analysis=analysis,
                image_detail=Config.IMAGE_DETAIL,
                model=Config.LLM_MODEL,
                search_metadata=search_metadata,
                llm_raw_response=llm_raw_response,
                detailed_search_logs=detailed_search_logs,
                make_query_tokens=make_query_tokens,
                analysis_tokens=analysis_tokens,
            )

            return AnalysisResponse(
                status="success",
                analysis=analysis,
                references=references
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
