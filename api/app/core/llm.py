"""
LLM 모듈
"""
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import Config


def get_llm():
    """LLM 인스턴스 생성 및 반환"""
    # 모델명으로 제공자 자동 선택
    if Config.LLM_MODEL.startswith("gemini"):
        return ChatGoogleGenerativeAI(
            model=Config.LLM_MODEL,
            google_api_key=Config.GEMINI_API_KEY
        )
    elif Config.LLM_MODEL.startswith("gpt"):
        return ChatOpenAI(
            model=Config.LLM_MODEL,
            api_key=Config.OPENAI_API_KEY
        )
    else:
        raise ValueError(f"지원하지 않는 모델입니다: {Config.LLM_MODEL}")
