"""
RAG 체인 빌더 및 하이브리드 검색
"""
import logging
import hashlib
from typing import List, Dict, Any, Tuple
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document
from app.core.config import Config
from app.core.vision import format_docs, create_multimodal_message, extract_json

logger = logging.getLogger(__name__)


def _merge_with_rrf(dense_docs: List, sparse_docs: List, k: int = 60) -> Tuple[List, Dict[str, float]]:
    """RRF (Reciprocal Rank Fusion)로 두 리트리버 결과 병합

    Args:
        dense_docs: Dense 검색 결과 (벡터 유사도 기반)
        sparse_docs: Sparse 검색 결과 (BM25 기반)
        k: RRF k값 (기본 60)

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


def initialize_bm25_retriever(db_manager):
    """
    BM25 리트리버 초기화

    Args:
        db_manager: VectorStoreManager 인스턴스

    Returns:
        BM25Retriever 인스턴스 또는 None (초기화 실패 시)
    """
    try:
        all_results = db_manager.vectorstore.get()
        if all_results and all_results.get("documents"):
            all_docs = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(all_results["documents"], all_results["metadatas"])
            ]
            return db_manager.get_bm25_retriever(all_docs)
    except Exception as e:
        logger.warning(f"⚠️  BM25 리트리버 생성 실패: {e}")

    return None


def perform_hybrid_search(
    db_manager,
    bm25_retriever,
    queries: List[str]
) -> Tuple[List, Dict[str, float], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    여러 쿼리로 Dense + BM25 하이브리드 검색 수행 (상세 로깅 포함)

    Args:
        db_manager: VectorStoreManager 인스턴스
        bm25_retriever: BM25 리트리버 (None 가능)
        queries: 검색 쿼리 리스트 (e.g., ["쿼리1", "쿼리2", "쿼리3", "기본정보 기반 쿼리"])

    Returns:
        tuple: (search_results, rrf_scores, search_metadata, detailed_search_logs)
    """
    dense_all = []
    sparse_all = []
    dense_scores = {}
    sparse_scores = {}

    # 상세 로깅용: 쿼리별 결과
    detailed_search_logs = []

    # 모든 쿼리로 검색 (반복문으로 동적 처리)
    for query_idx, q in enumerate(queries, 1):
        logger.info(f"   [쿼리{query_idx}] {q[:60]}...")

        # Dense 검색
        dense_docs_with_scores = db_manager.vectorstore.similarity_search_with_score(q, k=5)
        dense_docs = [doc for doc, score in dense_docs_with_scores]
        dense_all.extend(dense_docs)

        # Dense 점수 기록
        query_dense_results = []
        for rank, (doc, score) in enumerate(dense_docs_with_scores, 1):
            source_key = doc.metadata.get("source", str(hash(doc.page_content)))
            if source_key not in dense_scores:
                dense_scores[source_key] = score
            query_dense_results.append({
                "rank": rank,
                "source": source_key,
                "score": float(score)
            })

        # BM25 검색
        query_sparse_results = []
        if bm25_retriever:
            sparse_docs = bm25_retriever.invoke(q)
            sparse_all.extend(sparse_docs)
            for rank, doc in enumerate(sparse_docs, 1):
                source_key = doc.metadata.get("source", str(hash(doc.page_content)))
                if source_key not in sparse_scores:
                    sparse_scores[source_key] = 1
                query_sparse_results.append({
                    "rank": rank,
                    "source": source_key,
                    "score": 1
                })

        # 쿼리별 결과 기록
        detailed_search_logs.append({
            "query_index": query_idx,
            "query_text": q,
            "dense_results": query_dense_results,
            "bm25_results": query_sparse_results
        })

        logger.info(f"      ├─ Dense: {len(query_dense_results)}개")
        logger.info(f"      └─ BM25: {len(query_sparse_results)}개")

    logger.info(f"   ✓ 총계 - Dense: {len(dense_all)}개, BM25: {len(sparse_all)}개")

    # RRF 병합
    if sparse_all:
        search_results, rrf_scores = _merge_with_rrf(dense_all, sparse_all, k=Config.RRF_K)
        logger.info(f"   ✓ RRF 병합 (k={Config.RRF_K}): {len(search_results)}개 문서")
    else:
        search_results = dense_all
        rrf_scores = dense_scores
        logger.info(f"   ✓ Dense만 사용")

    # 상위 10개로 제한
    search_results = search_results[:10]

    # 로깅용 메타데이터 생성
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

    return search_results, rrf_scores, search_metadata, detailed_search_logs


def _generate_optimized_query(llm, filled_make_query_prompt, image_url, image_detail):
    """
    LLM을 사용하여 최적화된 RAG 검색 쿼리 생성

    Args:
        llm: LLM 인스턴스
        filled_make_query_prompt: {user_query} 치환된 프롬프트
        image_url: 이미지 URL
        image_detail: 이미지 상세도

    Returns:
        dict: {
            "image_analysis": {"hair": ..., "skin": ..., "contour": ...},
            "search_query": "..."
        } 또는 None (실패 시)
    """
    # LLM에 전달할 메시지 구성 (이미지 + 프롬프트)
    message = HumanMessage(
        content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": image_detail,
                },
            },
            {
                "type": "text",
                "text": filled_make_query_prompt,
            },
        ]
    )

    # LLM 호출
    logger.info("🔄 LLM으로 최적화된 검색 쿼리 생성 중...")
    response = llm.invoke([message], temperature=Config.ANALYSIS_TEMPERATURE)
    # AIMessage를 문자열로 변환
    response_text = response.content if hasattr(response, 'content') else str(response)
    logger.info(f"   ✅ 쿼리 생성 완료")

    # JSON 파싱
    try:
        query_result = extract_json(response_text)
        optimized_query = query_result.get("search_query", "")
        image_analysis = query_result.get("image_analysis", {})

        if not optimized_query:
            logger.warning("⚠️  생성된 쿼리가 비어있음, 원본 사용자 입력 사용")
            return None

        logger.info(f"   📝 생성된 쿼리: {optimized_query[:100]}...")

        # 이미지 분석 결과와 쿼리 함께 반환
        return {
            "image_analysis": image_analysis,
            "search_query": optimized_query,
            "raw_response": query_result
        }
    except Exception as e:
        logger.warning(f"⚠️  쿼리 파싱 실패: {e}, 원본 사용자 입력 사용")
        return None


def build_analysis_chain(retriever, llm, analysis_prompt, make_query_prompt, user_state, image_url):
    """
    분석 체인 구성

    Args:
        retriever: 벡터 DB retriever
        llm: LLM 인스턴스
        analysis_prompt: 분석 시스템 프롬프트
        make_query_prompt: 쿼리 생성 프롬프트
        user_state: 사용자 상태
        image_url: 이미지 URL

    Returns:
        tuple: (LCEL 체인, QueryGenerator 인스턴스)
    """
    image_detail = Config.IMAGE_DETAIL

    # make_query_prompt에서 {user_query} 치환
    filled_make_query_prompt = make_query_prompt.format(user_query=user_state)

    # 최적화된 검색 쿼리 생성 + 결과 저장 클래스
    class QueryGenerator:
        """쿼리 생성 및 이미지 분석 결과 저장"""
        def __init__(self):
            self.image_analysis = None
            self.search_query = None
            self.raw_response = None

        def __call__(self, _):
            """쿼리 생성 실행"""
            result = _generate_optimized_query(
                llm,
                filled_make_query_prompt,
                image_url,
                image_detail
            )

            if result:
                self.image_analysis = result.get("image_analysis")
                self.search_query = result.get("search_query")
                self.raw_response = result.get("raw_response")
                logger.info(f"   💾 이미지 분석 결과 저장됨")
                return self.search_query
            else:
                logger.info(f"   📌 원본 사용자 입력 사용")
                return user_state

    query_generator = QueryGenerator()

    chain = (
        RunnableLambda(query_generator)  # Step 1: 최적화된 쿼리 생성 + 결과 저장
        | retriever  # Step 2: 최적화된 쿼리로 검색
        | RunnableLambda(format_docs)  # Step 3: 문서 포맷팅
        | RunnableLambda(
            lambda formatted_docs: {
                "formatted_docs": formatted_docs,
                "user_state": user_state,
                "image_url": image_url,
                "detail": image_detail,
                "analysis_prompt": analysis_prompt,
            }
        )
        | RunnableLambda(create_multimodal_message)  # Step 4: 멀티모달 메시지 생성
        | llm  # Step 5: 최종 분석
        | StrOutputParser()
    )
    return chain, query_generator
