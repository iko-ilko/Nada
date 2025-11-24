"""
분석 플로우 로깅 모듈
분석 결과와 메타데이터를 JSON 파일로 저장합니다.
"""
import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from app.core.config import Config

logger = logging.getLogger(__name__)


class ChainLogger:
    """분석 플로우 로깅"""

    def __init__(self, log_dir: str = None):
        """ChainLogger 초기화"""
        if log_dir is None:
            log_dir = Config.LOGS_DIR

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def save_analysis(
        self,
        image_url: str,
        user_state: str,
        search_results: List[Any],
        analysis: Dict[str, Any],
        image_detail: str,
        model: str = None,
        search_metadata: List[Dict[str, Any]] = None,
        llm_raw_response: Dict[str, Any] = None,
        detailed_search_logs: List[Dict[str, Any]] = None
    ) -> str:
        """분석 결과를 로그 파일에 저장합니다."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"analysis_{timestamp}.json"
        log_filepath = self.log_dir / log_filename

        papers_info = self._extract_papers_info(search_results, search_metadata)

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
                    "RRF_K": Config.RRF_K,
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
                    "llm_raw_response": llm_raw_response if llm_raw_response else None,
                    "detailed_search_logs": detailed_search_logs if detailed_search_logs else None,
                    "papers": papers_info,
                }
            },
            "analysis": analysis,
        }

        try:
            with open(log_filepath, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 로그 저장 완료: {log_filepath}")
            return str(log_filepath)

        except Exception as e:
            logger.error(f"❌ 로그 저장 실패: {e}")
            raise

    def _extract_papers_info(self, search_results: List[Any], search_metadata: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """검색된 논문들의 정보를 추출합니다."""
        papers_info = []

        for i, doc in enumerate(search_results, 1):
            # search_metadata에서 점수 정보 추출 (있으면)
            scores = {}
            if search_metadata and i - 1 < len(search_metadata):
                meta = search_metadata[i - 1]
                scores = {
                    "dense_score": meta.get("dense_score"),
                    "bm25_score": meta.get("bm25_score"),
                    "rrf_score": meta.get("rrf_score"),
                }

            paper_info = {
                "rank": i,
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", "Unknown"),
                **scores,  # Dense, BM25, RRF 점수 추가
                "content_preview": doc.page_content[:300] if hasattr(doc, 'page_content') else "",
                "full_content": doc.page_content if hasattr(doc, 'page_content') else "",
            }
            papers_info.append(paper_info)

        return papers_info
