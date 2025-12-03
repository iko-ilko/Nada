"""
LLM을 활용한 YouTube 영상 필터링 및 제목 개선
"""
import json
import logging
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


def filter_and_refine_title(
    title: str,
    llm: ChatOpenAI,
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    LLM을 활용해 필요성 판단 + 제목 개선

    Args:
        title: 원본 영상 제목
        llm: ChatOpenAI 인스턴스
        description: 영상 설명 (선택)
        model: 사용할 모델

    Returns:
        {
            "is_relevant": bool,
            "reason": str,
            "refined_title": str (필요하면)
        }
        또는 None (LLM 실패 시)
    """
    # 프롬프트 동적 구성
    prompt = f"""당신은 뷰티 및 헤어 관리 전문 콘텐츠 큐레이터입니다.

다음 YouTube 영상이 뷰티/헤어 코칭 서비스에 필요한 교육적 콘텐츠인지 판단하세요.

**영상 제목:** {title}
"""

    # description이 있으면 추가
    if description:
        prompt += f"""
**영상 설명:**
{description}
"""

    prompt += """
**판단 기준:**
1. 제목·설명에 얼굴/두상/피부/윤곽 개선과 직접적으로 관련된 키워드가 있는가?
   (예: 헤어, 두상, 피부, 보습, 여드름, 컨투어, 윤곽, 턱선, 마사지, 스트레칭, 얼굴 라인 등)
2. 제목·설명에 “방법/팁/루틴/원리/가이드/설명/튜토리얼” 같은 '실천 가능성'을 의미하는 단어가 포함되어 있는가?
3. 과학적/ 전문적 정보인가? 제목과 설명으로 실용적 조언이 있을지 판단.
4. 광고, 제품 판매, 브이로그, 연예인 따라잡기 같은 오락/일상/홍보 목적이 제목·설명에 드러나면 제외.
   (예: 브이로그, 데일리, 일상, 광고, 협찬, 쇼핑, 언박싱 등)

**응답 형식 (JSON):**
{
    "is_relevant": true/false,
    "reason": "판단 근거 (간단히)",
    "refined_title": "전문적으로 개선된 제목 (필요하면만, 불필요하면 null)"
}

필요하면 제목을 더 전문적이고 명확하게 다시 작성하세요.
단, 원본 의미는 유지하세요."""

    try:
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])

        # JSON 파싱
        content = response.content.strip()

        # ```json ... ``` 형식 처리
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]

        result = json.loads(content.strip())

        return {
            "is_relevant": result.get("is_relevant", False),
            "reason": result.get("reason", ""),
            "refined_title": result.get("refined_title")
        }

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON 파싱 실패: {str(e)}\n응답: {response.content if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"❌ LLM 필터링 실패: {str(e)}")
        return None
