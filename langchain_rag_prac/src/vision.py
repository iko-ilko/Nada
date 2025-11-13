"""
비전(Vision) 모듈
GPT-4o-mini의 이미지 분석 기능을 담당합니다.
LCEL (LangChain Expression Language)을 사용한 RAG 파이프라인.
"""
import json
import re
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from src.config import Config


class VisionAnalyzer:
    """
    이미지 분석을 담당하는 클래스
    LCEL을 사용한 RAG 파이프라인 구현
    """

    def __init__(self, retriever=None):
        """
        VisionAnalyzer 초기화

        Args:
            retriever: LangChain Retriever 객체 (vectorstore.as_retriever()로 생성)
        """
        self.llm = ChatOpenAI(
            model_name=Config.LLM_MODEL,
            temperature=Config.LLM_TEMPERATURE,
            api_key=Config.OPENAI_API_KEY
        )
        self.retriever = retriever
        self.image_detail = Config.IMAGE_DETAIL
        self.rag_chain = None
        print(f"✅ VisionAnalyzer 준비 완료 (디테일: {self.image_detail})")

    def _build_lcel_chain(self, system_prompt: str):
        """
        LCEL을 사용한 완전한 RAG + 멀티모달 LLM 체인

        파이프라인:
        1️⃣ Retriever: 문서 검색
        2️⃣ Format: 검색 결과를 텍스트로 변환
        3️⃣ Message Creation: JSON 메시지 객체 생성 (RunnableLambda)
        4️⃣ LLM: 멀티모달 분석 (이미지 + 텍스트)
        5️⃣ Parser: 문자열 추출
        """
        if self.retriever is None:
            raise ValueError("Retriever가 초기화되지 않았습니다")

        print(f"\n🔗 LCEL 완전 체인 구성 중...")

        # Step 1: 입력 준비 + RAG 실행
        def prepare_and_retrieve(inputs):
            """
            입력 dict에서 필드를 추출하고 RAG를 실행합니다.

            LCEL RunnableParallel의 각 key는 ORIGINAL INPUT을 받으므로,
            여기서 명시적으로 retriever를 호출합니다.
            """
            query = inputs.get("query", "") if isinstance(inputs, dict) else inputs

            # RAG 실행: retriever 호출
            search_results = self.retriever.invoke(query)
            formatted_docs = self._format_docs(search_results)

            return {
                "formatted_docs": formatted_docs,
                "user_state": inputs.get("user_state", "") if isinstance(inputs, dict) else "",
                "image_url": inputs.get("image_url", "") if isinstance(inputs, dict) else "",
                "detail": inputs.get("detail", "low") if isinstance(inputs, dict) else "low"
            }

        # Step 2: 멀티모달 메시지 생성 함수
        def create_multimodal_messages(prepared_inputs):
            """이미지 + RAG 컨텍스트를 포함한 메시지 생성"""
            return [
                SystemMessage(content=system_prompt),
                HumanMessage(content=[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": prepared_inputs["image_url"],
                            "detail": prepared_inputs["detail"]
                        }
                    },
                    {
                        "type": "text",
                        "text": self._build_final_prompt(
                            prepared_inputs["user_state"],
                            prepared_inputs["formatted_docs"],
                            prepared_inputs["image_url"]
                        )
                    }
                ])
            ]

        # Step 3: LCEL 직선형 파이프라인 구성
        # prepare_and_retrieve | create_multimodal_messages | llm | parser
        self.rag_chain = (
            RunnableLambda(prepare_and_retrieve)
            | RunnableLambda(create_multimodal_messages)
            | self.llm
            | StrOutputParser()
        )

        print(f"✅ LCEL 완전 체인 준비 완료")
        return self.rag_chain

    def analyze_image_with_context(
        self,
        image_url: str,
        system_prompt: str,
        user_state: str,
        search_query: str = None
    ) -> Dict[str, Any]:
        """
        LCEL RAG 파이프라인을 통해 이미지를 분석합니다.

        LCEL 파이프라인 구조:
        retriever | format_docs → (documents + metadata 전달)
                              ↓
                    multimodal message 구성
                              ↓
                         LLM 호출
                              ↓
                       JSON 추출

        Args:
            image_url: 분석할 이미지 URL
            system_prompt: 시스템 프롬프트 (분석 지침)
            user_state: 사용자 상태 설명 (예: "어제 라면 먹어서 부었어")
            search_query: RAG 검색 쿼리 (기본값: user_state)

        Returns:
            Dict: 분석 결과
                {
                    "analysis": {...},  # JSON 분석 결과
                    "image_url": str,
                    "model": str,
                    "detail": str,
                    "raw_response": str,
                    "search_results": List[Document]
                }
        """
        print(f"\n🔍 LCEL RAG 파이프라인으로 이미지 분석 중 (디테일: {self.image_detail})...")

        if search_query is None:
            search_query = user_state

        try:
            # 1️⃣ LCEL 체인 구성
            chain = self._build_lcel_chain(system_prompt)
            print(f"\n🚀 LCEL 체인 실행: {search_query}")

            # 2️⃣ LCEL 체인 실행 (모든 단계가 하나의 invoke 호출로 처리)
            raw_response = chain.invoke({
                "user_state": user_state,
                "image_url": image_url,
                "detail": self.image_detail,
                "query": search_query  # retriever 입력
            })

            print(f"✅ LCEL 체인 실행 완료")

            # 3️⃣ 메타데이터용 검색 결과 별도 저장
            search_results = self.retriever.invoke(search_query)
            print(f"   {len(search_results)}개 문서 검색됨")

            # 4️⃣ JSON 추출
            print(f"\n📋 JSON 추출 중...")
            analysis = self._extract_json(raw_response)

            result = {
                "analysis": analysis,
                "image_url": image_url,
                "model": Config.LLM_MODEL,
                "detail": self.image_detail,
                "raw_response": raw_response,
                "search_results": search_results
            }

            print(f"✅ LCEL RAG 파이프라인 완료")
            return result

        except Exception as e:
            print(f"❌ 이미지 분석 중 오류: {e}")
            raise

    def _build_final_prompt(self, user_state: str, formatted_docs: str, image_url: str) -> str:
        """최종 프롬프트 구성"""
        prompt = f"""이미지 분석 요청

사용자 상태: {user_state}

검색된 관련 문서:
{formatted_docs}

위 정보를 바탕으로 이미지를 분석하고 JSON 형식으로 답변해주세요."""

        return prompt

    def _format_docs(self, docs: List) -> str:
        """검색된 문서를 텍스트로 포맷팅"""
        if not docs:
            return "검색된 문서가 없습니다."

        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            content = doc.page_content[:200] if hasattr(doc, 'page_content') else str(doc)[:200]
            formatted.append(f"{i}. {source}\n   내용: {content}...")

        return "\n".join(formatted)

    def change_detail_level(self, new_detail: str) -> None:
        """
        이미지 디테일 레벨 변경

        Args:
            new_detail: "low" 또는 "high"

        Raises:
            ValueError: 유효하지 않은 디테일 레벨
        """
        valid_options = ["low", "high"]
        if new_detail not in valid_options:
            raise ValueError(
                f"디테일 레벨은 {valid_options} 중 하나여야 합니다. "
                f"받은 값: {new_detail}"
            )

        self.image_detail = new_detail
        print(f"✅ 이미지 디테일 레벨 변경: {new_detail}")


    def _extract_json(self, content: str) -> Dict[str, Any]:
        """
        응답에서 JSON을 추출합니다.

        Args:
            content: LLM 응답 텍스트

        Returns:
            Dict: 추출된 JSON 객체

        Raises:
            ValueError: JSON 추출 실패
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
