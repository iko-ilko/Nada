"""
비전(Vision) 모듈
LLM에 전달할 멀티모달 메시지 구성 함수들
"""
import json
import logging
import re
import os
from pathlib import Path
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models import BaseLanguageModel
from app.core.config import Config

logger = logging.getLogger(__name__)


def format_docs(docs: List) -> str:
    """검색된 문서를 텍스트로 포맷팅"""
    if not docs:
        return "검색된 문서가 없습니다."

    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "")
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        page_info = f" (p.{page})" if page else ""
        formatted.append(f"[{i}] {source}{page_info}\n{content}")

    return "\n---\n".join(formatted)


def build_final_prompt(user_state: str, formatted_docs: str) -> str:
    """사용자 상태와 검색된 문서를 결합한 프롬프트 텍스트 구성"""
    prompt = f"""사용자 상태: {user_state}

참고 자료:
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
            "analysis_prompt": str
        }

    Returns:
        List: [SystemMessage, HumanMessage]
    """
    formatted_docs = inputs.get("formatted_docs", "")
    user_state = inputs.get("user_state", "")
    image_url = inputs.get("image_url", "")
    detail = inputs.get("detail", "low")
    analysis_prompt = inputs.get("analysis_prompt", "")

    prompt_text = build_final_prompt(user_state, formatted_docs)

    return [
        SystemMessage(content=analysis_prompt),
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

    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    brace_pattern = r'\{.*\}'
    matches = re.findall(brace_pattern, content, re.DOTALL)

    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    logger.warning(f"⚠️  JSON 추출 실패. 원본 응답 반환")
    return {
        "raw_response": content,
        "error": "JSON 추출 실패",
        "parsing_attempted": True
    }


def analyze_image_and_create_multi_queries(vision_llm: BaseLanguageModel, image_base64: str, user_query: str, make_query_prompt: str = None) -> Dict[str, Any]:
    """
    이미지 분석과 3개의 검색 쿼리를 한 번의 API 호출로 동시 처리

    Args:
        vision_llm: Vision 능력이 있는 LLM 객체
        image_base64: Base64 인코딩된 이미지
        user_query: 사용자 질문
        make_query_prompt: 프롬프트 텍스트 (선택사항, make_query_ko.prt 내용)

    Returns:
        Dict: {
            "image_analysis": {"hair": "...", "skin": "...", "contour": "..."},
            "search_queries": ["쿼리1", "쿼리2", "쿼리3"]
        }
    """
    # 프롬프트 로드 (전달되지 않으면 기본값 사용)
    if make_query_prompt is None:
        project_root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
        prompt_path = project_root / "app/core/prompt/make_query_ko.prt"
        make_query_prompt = prompt_path.read_text(encoding="utf-8")

    # 프롬프트에 사용자 질문 삽입
    combined_prompt = make_query_prompt.replace("{user_query}", user_query)

    message = HumanMessage(
        content=[
            {"type": "text", "text": combined_prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            }
        ]
    )

    # temperature 오버라이드
    response = vision_llm.invoke([message], temperature=Config.MAKE_QUERY_TEMPERATURE)

    # 토큰 정보 추출
    total_tokens = 0
    if hasattr(response, 'response_metadata'):
        usage = response.response_metadata.get('token_usage', {})
        total_tokens = usage.get('total_tokens', 0)

    # JSON 파싱
    content = response.content
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)

    if json_match:
        result = json.loads(json_match.group(1))
    else:
        result = json.loads(content)

    # 딕셔너리 그대로 사용
    search_queries = result.get("search_queries", {})

    logger.info(f"✅ 이미지 분석 + 카테고리별 쿼리 생성 완료")
    logger.info(f"   - 헤어: {search_queries.get('hair', '')}")
    logger.info(f"   - 피부: {search_queries.get('skin', '')}")
    logger.info(f"   - 윤곽: {search_queries.get('contour', '')}")

    return {
        "image_analysis": result["image_analysis"],
        "search_queries": search_queries,
        "total_tokens": total_tokens
    }


def analyze_image(vision_llm: BaseLanguageModel, image_base64: str, analyze_prompt: str = None) -> Dict[str, Any]:
    """
    이미지 분석만 수행

    Args:
        vision_llm: Vision 능력이 있는 LLM 객체
        image_base64: Base64 인코딩된 이미지
        analyze_prompt: 프롬프트 텍스트 (선택사항, analyze_image_ko.prt 내용)

    Returns:
        Dict: {
            "image_analysis": {"basic_info": "...", "hair": "...", "skin": "...", "contour": "..."},
            "total_tokens": int
        }
    """
    # 프롬프트 로드
    if analyze_prompt is None:
        project_root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
        prompt_path = project_root / "app/core/prompt/analyze_image_ko.prt"
        analyze_prompt = prompt_path.read_text(encoding="utf-8")

    message = HumanMessage(
        content=[
            {"type": "text", "text": analyze_prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            }
        ]
    )

    # LLM 호출
    response = vision_llm.invoke([message], temperature=Config.MAKE_QUERY_TEMPERATURE)

    # 토큰 정보 추출
    total_tokens = 0
    if hasattr(response, 'response_metadata'):
        usage = response.response_metadata.get('token_usage', {})
        total_tokens = usage.get('total_tokens', 0)

    # JSON 파싱
    content = response.content
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)

    if json_match:
        result = json.loads(json_match.group(1))
    else:
        result = json.loads(content)

    logger.info(f"✅ 이미지 분석 완료 (토큰: {total_tokens})")

    return {
        "image_analysis": result["image_analysis"],
        "total_tokens": total_tokens
    }


def create_search_queries(vision_llm: BaseLanguageModel, image_analysis: Dict, user_query: str, make_query_prompt: str = None) -> Dict[str, Any]:
    """
    이미지 분석 결과를 바탕으로 검색 쿼리 생성

    Args:
        vision_llm: LLM 객체
        image_analysis: 이미지 분석 결과
        user_query: 사용자 질문
        make_query_prompt: 프롬프트 텍스트 (선택사항, make_query_ko.prt 내용)

    Returns:
        Dict: {
            "search_queries": ["쿼리1", "쿼리2", "쿼리3", "쿼리4"],
            "total_tokens": int
        }
    """
    # 프롬프트 로드
    if make_query_prompt is None:
        project_root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
        prompt_path = project_root / "app/core/prompt/make_query_ko.prt"
        make_query_prompt = prompt_path.read_text(encoding="utf-8")

    # 이미지 분석 결과를 텍스트로 변환
    analysis_text = f"""- 기본 정보: {image_analysis.get('basic_info', '')}
- 헤어: {image_analysis.get('hair', '')}
- 피부: {image_analysis.get('skin', '')}
- 윤곽: {image_analysis.get('contour', '')}"""

    # 프롬프트에 이미지 분석 결과와 사용자 질문 삽입
    combined_prompt = make_query_prompt.replace("{image_analysis}", analysis_text)
    combined_prompt = combined_prompt.replace("{user_query}", user_query)

    message = HumanMessage(content=[{"type": "text", "text": combined_prompt}])

    # LLM 호출
    response = vision_llm.invoke([message], temperature=Config.MAKE_QUERY_TEMPERATURE)

    # 토큰 정보 추출
    total_tokens = 0
    if hasattr(response, 'response_metadata'):
        usage = response.response_metadata.get('token_usage', {})
        total_tokens = usage.get('total_tokens', 0)

    # JSON 파싱
    content = response.content
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)

    if json_match:
        result = json.loads(json_match.group(1))
    else:
        result = json.loads(content)

    # basic_info를 기반으로 4번째 쿼리 생성 (나이대, 성별, 분위기)
    basic_info = image_analysis.get("basic_info", "")
    search_queries = result.get("search_queries", [])
    search_queries.append(basic_info)

    logger.info(f"✅ {len(search_queries)}개 검색 쿼리 생성 완료 (토큰: {total_tokens})")
    for i, query in enumerate(search_queries, 1):
        logger.info(f"   - 쿼리{i}: {query}")

    return {
        "search_queries": search_queries,
        "total_tokens": total_tokens
    }
