"""
LLM 모듈
"""
from langchain_openai import ChatOpenAI
from src.config import Config


def get_llm():
    """LLM 인스턴스 생성 및 반환"""
    return ChatOpenAI(model=Config.LLM_MODEL, temperature=Config.LLM_TEMPERATURE, api_key=Config.OPENAI_API_KEY)
