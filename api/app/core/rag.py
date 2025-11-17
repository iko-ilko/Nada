"""
RAG 체인 빌더
"""
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from app.core.vision import format_docs, create_multimodal_message


def build_analysis_chain(retriever, llm, system_prompt, user_state, image_url, image_detail):
    """
    분석 체인 구성

    Args:
        retriever: 벡터 DB retriever
        llm: LLM 인스턴스
        system_prompt: 시스템 프롬프트
        user_state: 사용자 상태
        image_url: 이미지 URL
        image_detail: 이미지 상세도

    Returns:
        LCEL 체인
    """
    chain = (
        retriever
        | RunnableLambda(format_docs)
        | RunnableLambda(
            lambda formatted_docs: {
                "formatted_docs": formatted_docs,
                "user_state": user_state,
                "image_url": image_url,
                "detail": image_detail,
                "system_prompt": system_prompt,
            }
        )
        | RunnableLambda(create_multimodal_message)
        | llm
        | StrOutputParser()
    )
    return chain
