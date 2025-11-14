"""
비전(Vision) 모듈
LLM에 전달할 멀티모달 메시지 구성 함수들
"""
import json
import re
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseLanguageModel


def format_docs(docs: List) -> str:
    """검색된 문서를 텍스트로 포맷팅"""
    if not docs:
        return "검색된 문서가 없습니다."

    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        content = doc.page_content[:200] if hasattr(doc, 'page_content') else str(doc)[:200]
        formatted.append(f"{i}. {source}\n   내용: {content}...")

    return "\n".join(formatted)


def build_final_prompt(user_state: str, formatted_docs: str) -> str:
    """사용자 상태와 검색된 문서를 결합한 프롬프트 텍스트 구성"""
    prompt = f"""사용자 상태: {user_state}

검색된 관련 문서:
{formatted_docs}"""

    return prompt


def create_multimodal_message(inputs: Dict[str, Any]) -> List:
    """이미지 + RAG 컨텍스트를 포함한 메시지 생성

    Args:
        inputs: {
            "formatted_docs": str,
            "user_state": str,
            "image_url": str,
            "detail": str,
            "system_prompt": str
        }

    Returns:
        List: [SystemMessage, HumanMessage]
    """
    formatted_docs = inputs.get("formatted_docs", "")
    user_state = inputs.get("user_state", "")
    image_url = inputs.get("image_url", "")
    detail = inputs.get("detail", "low")
    system_prompt = inputs.get("system_prompt", "")

    prompt_text = build_final_prompt(user_state, formatted_docs)

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": detail
                }
            },
            {
                "type": "text",
                "text": prompt_text
            }
        ])
    ]


def extract_json(content: str) -> Dict[str, Any]:
    """
    응답에서 JSON을 추출합니다.

    Args:
        content: LLM 응답 텍스트

    Returns:
        Dict: 추출된 JSON 객체
    """
    if not content:
        raise ValueError("빈 응답입니다")

    # 1. 전체 텍스트가 JSON인지 확인
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    # 2. { ... } 패턴으로 JSON 객체 찾기
    brace_pattern = r'\{.*\}'
    matches = re.findall(brace_pattern, content, re.DOTALL)

    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # 3. 추출 실패 시 경고
    print(f"⚠️  JSON 추출 실패. 원본 응답 반환")
    return {
        "raw_response": content,
        "error": "JSON 추출 실패",
        "parsing_attempted": True
    }
