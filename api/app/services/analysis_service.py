"""
분석 서비스
"""
import os
import logging
import hashlib
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


def _merge_with_rrf(dense_docs, sparse_docs, k=60):
    """RRF (Reciprocal Rank Fusion)로 두 리트리버 결과 병합

    Returns:
        tuple: (merged_docs, rrf_scores_dict)
            - merged_docs: RRF 점수 순으로 정렬된 Document 리스트
            - rrf_scores_dict: {source_key: rrf_score} 딕셔너리
    """
    scores = {}

    def add_results(docs):
        for rank, doc in enumerate(docs):
            # content 기반 해시로 중복 제거
            content_hash = hashlib.md5(doc.page_content.encode()).hexdigest()
            score = 1 / (k + rank + 1)
            if content_hash not in scores:
                scores[content_hash] = {"doc": doc, "score": 0}
            scores[content_hash]["score"] += score

    add_results(dense_docs)
    add_results(sparse_docs)

    # 점수 순으로 정렬
    merged = sorted(scores.values(), key=lambda x: x["score"], reverse=True)

    # source 기준 점수 딕셔너리 생성 (정렬 순서 유지)
    rrf_scores = {}
    for rank, item in enumerate(merged):
        doc = item["doc"]
        source_key = doc.metadata.get("source", f"doc_{rank}")
        rrf_scores[source_key] = item["score"]

    return [item["doc"] for item in merged], rrf_scores


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

            # 2. 하이브리드 검색 (Dense + BM25 + RRF)
            logger.info("🔍 하이브리드 검색 시작...")

            # Dense 검색
            dense_docs_with_scores = self.db_manager.vectorstore.similarity_search_with_score(
                request.user_state,
                k=Config.TOP_K
            )
            dense_docs = [doc for doc, score in dense_docs_with_scores]
            dense_scores = {doc.metadata.get("source", str(i)): score for i, (doc, score) in enumerate(dense_docs_with_scores)}
            logger.info(f"   ✓ Dense: {len(dense_docs)}개 문서")

            # BM25 검색
            if self.bm25_retriever is None:
                try:
                    # Chroma에서 모든 문서 가져오기
                    all_results = self.db_manager.vectorstore.get()
                    if all_results and all_results.get("documents"):
                        # 문자열과 메타데이터를 Document 객체로 변환
                        from langchain_core.documents import Document
                        all_docs = [
                            Document(page_content=doc, metadata=meta)
                            for doc, meta in zip(all_results["documents"], all_results["metadatas"])
                        ]
                        self.bm25_retriever = self.db_manager.get_bm25_retriever(all_docs)
                    else:
                        logger.warning("⚠️  BM25 문서 없음, Dense만 사용")
                        self.bm25_retriever = None
                except Exception as e:
                    logger.warning(f"⚠️  BM25 리트리버 생성 실패: {e}, Dense만 사용")
                    self.bm25_retriever = None

            sparse_docs = []
            sparse_scores = {}
            if self.bm25_retriever:
                sparse_docs = self.bm25_retriever.invoke(request.user_state)
                logger.info(f"   ✓ BM25: {len(sparse_docs)}개 문서")

            # RRF 병합
            rrf_scores = {}
            if sparse_docs:
                search_results, rrf_scores = _merge_with_rrf(dense_docs, sparse_docs, k=Config.RRF_K)
                logger.info(f"   ✓ RRF 병합: {len(search_results)}개 문서")
            else:
                search_results = dense_docs
                logger.info(f"   ✓ Dense만 사용")
                rrf_scores = dense_scores

            # 상위 7개로 제한
            search_results = search_results[:Config.TOP_K]

            # 3. 체인 구성
            retriever = self.db_manager.get_retriever()
            chain, query_generator = build_analysis_chain(
                retriever=retriever,
                llm=self.llm,
                analysis_prompt=self.analysis_prompt,
                make_query_prompt=self.make_query_prompt,
                user_state=request.user_state,
                image_url=image_url,
            )

            # 4. 체인 실행 (이미 검색한 문서들을 사용하도록 수정 가능)
            # 현재는 기존 retriever 사용, 추후 검색 결과를 직접 전달 가능
            raw_response = chain.invoke(request.user_state)

            # 5. JSON 추출
            analysis = extract_json(raw_response)

            # 6. LLM 원본 응답 추출 (이미지 분석 및 쿼리 생성 결과)
            llm_raw_response = query_generator.raw_response if query_generator.raw_response else {}

            # 7. 참고문헌 추출 (source 목록)
            references = [doc.metadata.get("source", f"doc_{i}") for i, doc in enumerate(search_results)]

            # 8. 로깅용 정보 준비 (Dense, BM25, RRF 점수)
            search_metadata = []
            for i, doc in enumerate(search_results):
                source_key = doc.metadata.get("source", f"doc_{i}")
                search_metadata.append({
                    "rank": i + 1,
                    "source": source_key,
                    "dense_score": dense_scores.get(source_key, None),
                    "bm25_score": sparse_scores.get(source_key, None),
                    "rrf_score": rrf_scores.get(source_key, None),
                })

            # 7. 로그 저장
            log_path = self.logger.save_analysis(
                image_url=image_url,
                user_state=request.user_state,
                search_results=search_results,
                analysis=analysis,
                image_detail=Config.IMAGE_DETAIL,
                model=Config.LLM_MODEL,
                search_metadata=search_metadata,
                llm_raw_response=llm_raw_response,
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
