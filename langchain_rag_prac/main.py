"""
RAG 시스템 메인 파일
멀티모달 이미지 분석 파이프라인을 실행합니다.
"""
from pathlib import Path
import sys
import os

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ['PROJECT_ROOT'] = str(project_root)

from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser

from src.config import Config
from src.indexer import DocumentIndexer, EmbeddingManager, VectorStoreManager
from src.vision import format_docs, create_multimodal_message, extract_json
from src.logger import AnalysisLogger
from src.llm import get_llm


def setup_vectorstore():
    """
    벡터 DB 준비
    기존 DB가 있으면 재구성 여부를 묻고, 없으면 자동 생성
    """
    print("=" * 60)
    print("📚 벡터 DB 준비 중...")
    print("=" * 60)

    Config.validate()

    indexer = DocumentIndexer()

    # 기존 벡터 DB 확인
    if os.path.exists(Config.CHROMA_DB_PATH):
        response = input("벡터 DB를 재구성하시겠습니까? (y/n): ").strip().lower()
        if response != 'y':
            # 기존 DB 사용
            return indexer.get_or_create_vectorstore()

    # 새로 생성
    return indexer.build_vectorstore()


def load_prompt(filename: str) -> str:
    """프로젝트 루트 기준으로 프롬프트 파일 로드"""
    project_root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
    prompt_path = project_root / filename
    text = prompt_path.read_text(encoding="utf-8")
    return text


def main(
    image_url: str = "https://res.cloudinary.com/nadacloud/image/upload/v1756530521/qmfzfedoxpkt1phjn1ag.jpg",
    user_state: str = "어제 저녁에 라면을 먹어서 부은것같아",
    image_detail: str = "low"
):
    """
    이미지를 분석하고 미용 코칭을 제공합니다.

    Args:
        image_url: 분석할 이미지 URL
        user_state: 사용자 상태 설명
        image_detail: 이미지 디테일 레벨 ("low" 또는 "high")
    """
    # 벡터 DB 준비
    setup_vectorstore()

    # 이미지 디테일 설정 (필요시)
    if image_detail != Config.IMAGE_DETAIL:
        Config.IMAGE_DETAIL = image_detail

    # 분석 파라미터
    print(f"\n📝 분석 요청:")
    print(f"   이미지: {image_url[:50]}...")
    print(f"   상태: {user_state}")
    print(f"   디테일: {image_detail}")

    # 분석 파이프라인 준비
    print(f"\n🔧 분석 파이프라인 준비...")
    embedding_manager = EmbeddingManager()
    embeddings = embedding_manager.get_embeddings()

    db_manager = VectorStoreManager(embeddings)
    try:
        db_manager.load_vectorstore()
    except Exception as e:
        print(f"❌ 벡터 DB 로드 실패: {e}")
        return

    retriever = db_manager.get_retriever()
    system_prompt = load_prompt("src/prompt/response_ko.prt")

    # LLM 설정
    llm = get_llm()

    # LCEL 체인 구성: 각 단계가 명확한 책임을 가짐
    chain = (
        retriever  # 1. retriever: user_state로 문서 검색
        | RunnableLambda(format_docs)  # 2. format_docs: 검색 결과 포맷팅
        | RunnableLambda(
            lambda formatted_docs: {
                "formatted_docs": formatted_docs,
                "user_state": user_state,
                "image_url": image_url,
                "detail": image_detail,
                "system_prompt": system_prompt,
            }
        )  # 3. 딕셔너리 구성
        | RunnableLambda(create_multimodal_message)  # 4. 메시지 생성
        | llm  # 5. LLM 호출
        | StrOutputParser()  # 6. 응답 파싱
    )

    # 파이프라인 실행
    print(f"\n{'='*60}")
    print("🚀 분석 시작")
    print(f"{'='*60}")

    try:
        # 체인 호출: retriever가 첫 단계이므로 user_state 문자열만 전달
        raw_response = chain.invoke(user_state)

        # JSON 추출
        analysis = extract_json(raw_response)

        # 검색 결과 가져오기 (결과 출력용)
        search_results = retriever.invoke(user_state)

        # 결과 출력
        print(f"\n{'='*60}")
        print("📊 분석 결과")
        print(f"{'='*60}")

        # 검색된 문서
        print(f"\n📚 검색된 문서 ({len(search_results)}개):")
        papers_info = _extract_papers_info(search_results)
        if papers_info:
            for paper in papers_info:
                print(f"\n   [{paper['rank']}] {paper['source']}")
                print(f"       페이지: {paper['page']} | 타입: {paper['type']}")
                print(f"       미리보기: {paper['content_preview'][:100]}...")
        else:
            print(f"   검색된 문서가 없습니다.")

        # LLM 분석 결과
        print(f"\n🤖 분석:")
        print(f"   모델: {Config.LLM_MODEL}")
        print(f"   이미지 디테일: {image_detail}")

        import json
        if isinstance(analysis, dict):
            print(json.dumps(analysis, indent=4, ensure_ascii=False))
        else:
            print(analysis)

        # 결과 저장
        logger = AnalysisLogger()
        log_path = logger.save_analysis(
            image_url=image_url,
            user_state=user_state,
            search_results=search_results,
            analysis=analysis,
            image_detail=image_detail,
            model=Config.LLM_MODEL
        )

        print(f"\n💾 저장:")
        print(f"   {log_path}")

        print(f"\n{'='*60}")
        print(f"✅ 완료!")
        print(f"{'='*60}")

        return {
            "image_url": image_url,
            "user_state": user_state,
            "search_results": search_results,
            "papers_info": papers_info,
            "analysis": analysis,
            "model": Config.LLM_MODEL,
            "image_detail": image_detail,
            "raw_response": raw_response,
            "log_path": log_path
        }

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


def _extract_papers_info(search_results):
    """
    검색된 논문들의 정보를 추출합니다.

    Args:
        search_results: Document 객체 리스트

    Returns:
        List: 논문 정보 리스트
    """
    papers_info = []

    for i, doc in enumerate(search_results, 1):
        paper_info = {
            "rank": i,
            "source": doc.metadata.get("source", "Unknown"),
            "type": doc.metadata.get("type", "Unknown"),
            "page": doc.metadata.get("page", "Unknown"),
            "content_preview": doc.page_content[:300] if hasattr(doc, 'page_content') else "",
            "full_content": doc.page_content if hasattr(doc, 'page_content') else "",
        }
        papers_info.append(paper_info)

    return papers_info


if __name__ == "__main__":
    # 멀티모달 RAG 실행 (벡터 DB가 없으면 자동 생성)
    main(
        image_url="https://res.cloudinary.com/nadacloud/image/upload/v1756530521/qmfzfedoxpkt1phjn1ag.jpg",
        # user_state="머리색을 바꾸고 싶은데 나한테 어울리는게 뭘까?",
        # user_state="어제 저녁에 라면을 먹어서 부은것같아",
        # user_state="얼굴이 처져 보이는데 개선 방법이 있을까?",
        user_state="피부가 더 좋아지고 싶어.",
        image_detail="low"
    )
