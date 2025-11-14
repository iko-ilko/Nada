"""
로깅 모듈
분석 결과와 메타데이터를 JSON 파일로 저장합니다.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from src.config import Config


class AnalysisLogger:
    """분석 결과 로깅"""

    def __init__(self, log_dir: str = None):
        """
        AnalysisLogger 초기화

        Args:
            log_dir: 로그 저장 디렉토리 (기본값: PROJECT_ROOT/logs)
        """
        if log_dir is None:
            project_root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
            log_dir = str(project_root / "logs")

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def save_analysis(
        self,
        image_url: str,
        user_state: str,
        search_results: List[Any],
        analysis: Dict[str, Any],
        image_detail: str,
        model: str = None  # Config에서 가져올 수 있으므로 옵션
    ) -> str:
        """분석 결과를 로그 파일에 저장합니다."""
        # 타임스탬프
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"analysis_{timestamp}.json"
        log_filepath = self.log_dir / log_filename

        # 검색된 논문 정보 추출
        papers_info = self._extract_papers_info(search_results)

        # 로그 데이터 구성
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "config": {
                    "LLM_MODEL": Config.LLM_MODEL,
                    "EMBEDDING_MODEL": Config.EMBEDDING_MODEL,
                    "IMAGE_DETAIL": image_detail,
                    "CHUNK_SIZE": Config.CHUNK_SIZE,
                    "CHUNK_OVERLAP": Config.CHUNK_OVERLAP,
                    "TOP_K": Config.TOP_K,
                },
                "image": {
                    "url": image_url,
                    "detail_level": image_detail,
                },
                "input": {
                    "user_state": user_state,
                },
                "search": {
                    "total_results": len(search_results),
                    "papers": papers_info,
                }
            },
            "analysis": analysis,
        }

        # JSON으로 저장
        try:
            with open(log_filepath, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 로그 저장 완료: {log_filepath}")
            return str(log_filepath)

        except Exception as e:
            print(f"❌ 로그 저장 실패: {e}")
            raise

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
