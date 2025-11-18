"""
RAG 체인 빌더
"""
import logging
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from app.core.config import Config
from app.core.vision import format_docs, create_multimodal_message, extract_json

logger = logging.getLogger(__name__)


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
    response = llm.invoke([message])
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
