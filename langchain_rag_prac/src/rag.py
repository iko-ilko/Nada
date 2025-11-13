"""
RAG 모듈
Retrieval-Augmented Generation 파이프라인
"""
from typing import Dict, Any, List
from src.vision import VisionAnalyzer
from src.logger import AnalysisLogger


class MultimodalRAGChain:
    """
    멀티모달 RAG 체인
    이미지 + 텍스트 상태 + RAG 검색 결과를 통합해서 처리
    """

    def __init__(self, retriever):
        """
        MultimodalRAGChain 초기화

        Args:
            retriever: 벡터 검색기 (LangChain Retriever 객체)
        """
        self.retriever = retriever
        self.vision_analyzer = VisionAnalyzer(retriever=retriever)
        self.logger = AnalysisLogger()
        print(f"✅ MultimodalRAGChain 준비 완료")

    def query_with_image_and_state(
        self,
        image_url: str,
        user_state: str,
        system_prompt: str
    ) -> Dict[str, Any]:
        """
        이미지와 사용자 상태를 기반으로 RAG 파이프라인을 통해 분석합니다.

        RAG 파이프라인 흐름:
        1. user_state를 쿼리로 vectorstore에서 관련 문서 검색 (retriever 사용)
        2. 검색된 문서 포맷팅
        3. 이미지 + 포맷팅된 문서 + 시스템 프롬프트를 LLM에 전달
        4. LLM이 멀티모달 분석 수행

        Args:
            image_url: 분석할 이미지 URL
            user_state: 사용자 상태 설명 (예: "어제 라면 먹어서 부었어")
            system_prompt: 시스템 프롬프트 (분석 지침)

        Returns:
            Dict: 분석 결과
                {
                    "image_url": str,
                    "user_state": str,
                    "search_results": List[Document],  # RAG 검색 결과
                    "papers_info": List[Dict],  # 논문 메타데이터
                    "analysis": Dict,  # JSON 분석 결과
                    "model": str,
                    "image_detail": str,
                    "log_path": str  # 저장된 로그 파일 경로
                }
        """
        print("\n" + "=" * 60)
        print("🔄 멀티모달 RAG 파이프라인 시작")
        print("=" * 60)

        # RAG 파이프라인을 통한 분석
        # (VisionAnalyzer 내부에서 retriever를 사용해 검색 + LLM 호출)
        analysis_result = self.vision_analyzer.analyze_image_with_context(
            image_url=image_url,
            system_prompt=system_prompt,
            user_state=user_state,
            search_query=user_state
        )

        # 검색 결과에서 논문 정보 추출
        search_results = analysis_result.get("search_results", [])
        papers_info = self._extract_papers_info(search_results)

        # 결과 정리
        result = {
            "image_url": image_url,
            "user_state": user_state,
            "search_results": search_results,
            "papers_info": papers_info,
            "analysis": analysis_result["analysis"],
            "model": analysis_result["model"],
            "image_detail": analysis_result["detail"],
            "raw_response": analysis_result["raw_response"]
        }

        # 로깅
        log_path = self.logger.save_analysis(
            image_url=image_url,
            user_state=user_state,
            search_results=search_results,
            analysis=analysis_result["analysis"],
            image_detail=analysis_result["detail"],
            model=analysis_result["model"]
        )
        result["log_path"] = log_path

        print(f"\n" + "=" * 60)
        print("✅ 멀티모달 RAG 파이프라인 완료")
        print("=" * 60)

        return result

    def _extract_papers_info(self, search_results: List[Any]) -> List[Dict[str, str]]:
        """
        검색된 논문들의 정보를 추출합니다.

        Args:
            search_results: Document 객체 리스트

        Returns:
            List: 논문 정보 리스트 (RAG 컨텍스트 포함)
        """
        papers_info = []

        for i, doc in enumerate(search_results, 1):
            paper_info = {
                "rank": i,
                "source": doc.metadata.get("source", "Unknown"),
                "type": doc.metadata.get("type", "Unknown"),
                "page": doc.metadata.get("page", "Unknown"),
                "content_preview": doc.page_content[:300] if hasattr(doc, 'page_content') else "",
                # RAG 검증용: 실제 전달된 컨텍스트 포함
                "full_content": doc.page_content if hasattr(doc, 'page_content') else "",
            }
            papers_info.append(paper_info)

        return papers_info

    def change_image_detail(self, new_detail: str) -> None:
        """
        이미지 디테일 레벨 변경

        Args:
            new_detail: "low" 또는 "high"
        """
        self.vision_analyzer.change_detail_level(new_detail)

    def get_current_image_detail(self) -> str:
        """
        현재 이미지 디테일 레벨 반환

        Returns:
            str: "low" 또는 "high"
        """
        return self.vision_analyzer.image_detail
