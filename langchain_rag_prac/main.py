"""
RAG 시스템 메인 파일
모든 모듈을 조합해서 실행합니다.
"""
from pathlib import Path
import sys
import os

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ['PROJECT_ROOT'] = str(project_root)

from src.config import Config
from src.loader import DocumentLoader
from src.embedder import EmbeddingManager
from src.db import TextChunker, VectorStoreManager
from src.rag import MultimodalRAGChain


def main():
    """
    벡터 DB 준비 함수
    이미지와 상태를 받아서 멀티모달 RAG를 실행하기 위한 셋업
    """
    print("=" * 60)
    print("🔄 벡터 DB 준비 중...")
    print("=" * 60)

    # 설정 검증
    Config.validate()

    # 벡터 DB 폴더 존재 여부 확인
    vectorstore = None

    if os.path.exists(Config.CHROMA_DB_PATH):
        print(f"\n📂 기존 벡터 DB 발견: {Config.CHROMA_DB_PATH}")
        response = input("문서를 다시 로드하고 벡터 DB를 재구성하시겠습니까? (y/n): ").strip().lower()

        if response == 'n':
            # 기존 벡터 DB 사용
            print("✅ 기존 벡터 DB를 사용합니다")
            embedding_manager = EmbeddingManager()
            embeddings = embedding_manager.get_embeddings()
            db_manager = VectorStoreManager(embeddings)
            vectorstore = db_manager.load_vectorstore()
        # y 또는 기타 입력이면 계속 진행 (재구성)

    # 벡터 DB가 없거나 사용자가 재구성을 선택한 경우
    if vectorstore is None:
        # 1️⃣ 문서 로드
        print("\n1️⃣  문서 로드 중...")
        loader = DocumentLoader()
        documents = loader.load_documents()

        if len(documents) == 0:
            print("\n❌ 프로그램 종료")
            return

        # 2️⃣ 청킹
        print("\n2️⃣  문서 청킹 중...")
        chunker = TextChunker()
        chunks = chunker.chunk_documents(documents)

        # 3️⃣ 임베딩 + 벡터 DB
        print("\n3️⃣  벡터 DB 생성 중...")
        embedding_manager = EmbeddingManager()
        embeddings = embedding_manager.get_embeddings()

        db_manager = VectorStoreManager(embeddings)
        vectorstore = db_manager.create_vectorstore(chunks)

    print("\n✅ 벡터 DB 준비 완료!")
    print("=" * 60)


def load_prompt(path: str) -> str:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return text


def test_multimodal_rag(
    image_url: str = "https://res.cloudinary.com/nadacloud/image/upload/v1756530521/qmfzfedoxpkt1phjn1ag.jpg",
    user_state: str = "어제 저녁에 라면을 먹어서 부은것같아",
    image_detail: str = "low"
):
    """
    LCEL (LangChain Expression Language) 기반 멀티모달 RAG 파이프라인 테스트

    파이프라인 아키텍처 (LCEL 문법 사용):
    1. DocumentLoader → PDF 문서 로드
    2. TextChunker → 문서를 300토큰 청크로 분할
    3. EmbeddingManager → all-MiniLM-L12-v2 임베딩 생성
    4. VectorStoreManager → Chroma 벡터 DB 저장
    5. Retriever (as_retriever()) → vectorstore.as_retriever()로 생성
    6. LCEL Chain (retriever | format_docs) → pipe 연산자로 구성
    7. VisionAnalyzer + LLM → 이미지 + RAG 컨텍스트 멀티모달 분석
    8. MultimodalRAGChain → 전체 조율 및 로깅

    LCEL 핵심:
    - | (pipe) 연산자: 컴포넌트 연결
    - RunnableLambda: Python 함수를 Runnable로 변환
    - RunnablePassthrough: 값을 다음 단계로 전달

    Args:
        image_url: 분석할 이미지 URL
        user_state: 사용자 상태 설명
        image_detail: 이미지 디테일 레벨 ("low" 또는 "high")
    """
    print("\n" + "=" * 60)
    print("🔗 LCEL (LangChain Expression Language) RAG 파이프라인")
    print("=" * 60)

    # 설정
    Config.validate()

    # 이미지 디테일 설정 변경 (필요시)
    if image_detail != Config.IMAGE_DETAIL:
        print(f"\n⚙️  이미지 디테일 설정 변경: {Config.IMAGE_DETAIL} → {image_detail}")
        Config.IMAGE_DETAIL = image_detail

    print(f"\n📝 입력 파라미터:")
    print(f"   이미지 URL: {image_url[:50]}...")
    print(f"   사용자 상태: {user_state}")
    print(f"   이미지 디테일: {image_detail}")

    # LCEL 파이프라인 구성
    print(f"\n{'='*60}")
    print("🔄 LCEL 파이프라인 구성 중...")
    print(f"{'='*60}")

    # 1️⃣ 임베딩 모델 로드 (Embeddings Runnable)
    print(f"\n1️⃣ 임베딩 모델 로드")
    embedding_manager = EmbeddingManager()
    embeddings = embedding_manager.get_embeddings()

    # 2️⃣ 벡터 스토어 로드 (VectorStore)
    print(f"\n2️⃣ 벡터 스토어 로드")
    db_manager = VectorStoreManager(embeddings)

    if not os.path.exists(Config.CHROMA_DB_PATH):
        print(f"❌ 벡터 DB가 없습니다. main() 함수를 먼저 실행해주세요.")
        return

    vectorstore = db_manager.load_vectorstore()

    # 3️⃣ Retriever 생성 (LCEL Runnable)
    print(f"\n3️⃣ Retriever 생성: vectorstore.as_retriever()")
    print(f"   (LangChain Runnable 객체)")
    retriever = db_manager.get_retriever()
    print(f"   검색 타입: similarity")
    print(f"   Top-K: {Config.TOP_K}")
    print(f"   → Retriever: Runnable[str] → List[Document]")

    # 4️⃣ VisionAnalyzer에 Retriever 주입
    print(f"\n4️⃣ VisionAnalyzer 구성")
    print(f"   (retriever를 생성자로 주입)")
    print(f"   내부 LCEL 체인: retriever | RunnableLambda(format_docs)")

    # 5️⃣ MultimodalRAGChain 생성
    print(f"\n5️⃣ MultimodalRAGChain 구성")
    multimodal_chain = MultimodalRAGChain(retriever)

    # 6️⃣ 시스템 프롬프트 로드
    print(f"\n6️⃣ 시스템 프롬프트 로드")
    system_prompt = load_prompt("src/prompt/response_ko.prt")

    # LCEL 파이프라인 실행
    print(f"\n{'='*60}")
    print("🚀 LCEL 파이프라인 실행")
    print(f"{'='*60}")

    try:
        result = multimodal_chain.query_with_image_and_state(
            image_url=image_url,
            user_state=user_state,
            system_prompt=system_prompt
        )

        # LCEL 파이프라인 결과 출력
        print(f"\n{'='*60}")
        print("📊 LCEL 파이프라인 결과")
        print(f"{'='*60}")

        # 1️⃣ Retriever 단계 결과
        print(f"\n1️⃣ Retriever 출력 ({len(result['search_results'])}개 Document):")
        print(f"\n   [RAG 검증: 검색된 문서가 LLM에 컨텍스트로 전달되었는지 확인]")
        if result["papers_info"]:
            for paper in result["papers_info"]:
                print(f"\n   [{paper['rank']}] {paper['source']}")
                print(f"       페이지: {paper['page']} | 타입: {paper['type']}")
                print(f"       미리보기: {paper['content_preview'][:100]}...")
                # RAG 검증: 실제 전달된 내용의 길이 표시
                content_len = len(paper.get('full_content', ''))
                print(f"       ✅ 전달된 컨텍스트 길이: {content_len} 글자")
        else:
            print(f"   검색된 문서가 없습니다.")

        # 2️⃣ Format 단계 결과
        print(f"\n2️⃣ RunnableLambda(format_docs) 출력:")
        print(f"   (Retriever 결과를 텍스트로 포맷)")
        print(f"   길이: {len(result['papers_info'])} 개 문서 포함")

        # 3️⃣ LLM 단계 결과
        print(f"\n3️⃣ ChatOpenAI LLM 호출:")
        print(f"   입력: [SystemMessage, HumanMessage(image_url + formatted_docs)]")
        print(f"   모델: {result['model']}")
        print(f"   이미지 디테일: {result['image_detail']}")
        print(f"\n   LLM 분석 결과 (JSON):")

        import json

        if isinstance(result["analysis"], dict):
            print(json.dumps(result["analysis"], indent=4, ensure_ascii=False))
        else:
            print(result["analysis"])

        # 4️⃣ 최종 저장
        print(f"\n4️⃣ 결과 저장:")
        print(f"   로그 파일: {result['log_path']}")

        print(f"\n{'='*60}")
        print(f"✅ LCEL 파이프라인 실행 완료!")
        print(f"{'='*60}")

        return result

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 벡터 DB 준비
    main()

    # 멀티모달 RAG 실행
    test_multimodal_rag(
        image_url="https://res.cloudinary.com/nadacloud/image/upload/v1756530521/qmfzfedoxpkt1phjn1ag.jpg",
        # user_state="머리색을 바꾸고 싶은데 나한테 어울리는게 뭘까?",
        # user_state="어제 저녁에 라면을 먹어서 부은것같아",
        # user_state="얼굴이 처져 보이는데 개선 방법이 있을까?",
        user_state="피부가 더 좋아지고 싶어.",
        image_detail="low"
    )
