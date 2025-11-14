"""
문서 인덱싱 모듈
문서를 로드하고 청킹하여 벡터 DB에 저장합니다.

포함된 클래스:
- DocumentLoader: PDF/TXT 파일 로드
- TextChunker: 문서 청킹
- EmbeddingManager: 임베딩 모델 관리
- VectorStoreManager: 벡터 DB 관리
- DocumentIndexer: 전체 인덱싱 오케스트레이션
"""
import os
import time
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from src.config import Config


class DocumentLoader:
    """문서 로더: PDF와 TXT 파일을 로드합니다."""

    def __init__(self, folder_path=None):
        self.folder_path = folder_path or Config.DATA_DIR

    def load_documents(self):
        """폴더 안의 모든 PDF와 TXT 파일을 로드

        PDF 파일은 페이지들을 병합하여 한 문서로 만듭니다.
        (청킹 전에 페이지를 나누면 의미 있는 청킹이 불가능)
        """
        documents = []

        if not os.path.exists(self.folder_path):
            print(f"❌ 폴더 없음: {self.folder_path}")
            return documents

        pdf_files = list(Path(self.folder_path).glob("*.pdf"))
        txt_files = list(Path(self.folder_path).glob("*.txt"))

        print(f"\n📄 문서 로드 중... (PDF: {len(pdf_files)}, TXT: {len(txt_files)})")

        if len(pdf_files) == 0 and len(txt_files) == 0:
            print("⚠️  문서가 없습니다. PDF 또는 TXT 파일을 추가해주세요.")
            return documents

        # PDF 로드: 페이지들을 병합하여 한 문서로
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                pages = loader.load()

                if pages:
                    # 모든 페이지의 내용을 합침
                    merged_content = "\n\n".join([page.page_content for page in pages])

                    # 메타데이터는 첫 페이지 기준
                    merged_doc = pages[0]
                    merged_doc.page_content = merged_content
                    merged_doc.metadata["source"] = pdf_file.name
                    merged_doc.metadata["type"] = "pdf"
                    merged_doc.metadata["total_pages"] = len(pages)

                    documents.append(merged_doc)
            except Exception as e:
                print(f"   ❌ {pdf_file.name}: {e}")

        # TXT 로드
        for txt_file in txt_files:
            try:
                loader = TextLoader(str(txt_file), encoding="utf-8")
                docs = loader.load()

                for doc in docs:
                    doc.metadata["source"] = txt_file.name
                    doc.metadata["type"] = "txt"

                documents.extend(docs)
            except Exception as e:
                print(f"   ❌ {txt_file.name}: {e}")

        print(f"   ✅ {len(pdf_files) + len(txt_files)}개 파일에서 {len(documents)}개 문서 로드")
        return documents


class TextChunker:
    """문서 청킹: 긴 문서를 작은 청크로 분할합니다."""

    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or Config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP

    def chunk_documents(self, documents):
        """문서를 작은 청크로 분할"""
        print(f"\n✂️  청킹 중... (크기: {self.chunk_size}, 오버랩: {self.chunk_overlap})")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = splitter.split_documents(documents)
        print(f"   ✅ {len(chunks)}개 청크 생성")
        return chunks


class EmbeddingManager:
    """임베딩 관리자: 문서를 벡터로 변환합니다."""

    def __init__(self, model_name=None):
        self.model_name = model_name or Config.EMBEDDING_MODEL
        self.embeddings = None

    def get_embeddings(self):
        """임베딩 모델 로드 (처음 로드시만 다운로드)"""
        if self.embeddings is not None:
            return self.embeddings

        print(f"\n🔢 임베딩 모델 로드 중... ({self.model_name})")

        self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)

        print(f"   ✅ 준비 완료")
        return self.embeddings


class VectorStoreManager:
    """벡터 DB 관리자: Chroma 벡터 DB를 관리합니다."""

    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.persist_dir = Config.CHROMA_DB_PATH
        self.collection_name = "papers"
        self.vectorstore = None

    def create_vectorstore(self, chunks):
        """청크들을 임베딩하고 벡터 DB에 저장"""
        print(f"\n💾 벡터 DB 저장 중... ({len(chunks)}개 청크)")

        start_time = time.time()

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_dir,
            collection_name=self.collection_name
        )

        elapsed_time = time.time() - start_time
        print(f"   ✅ {elapsed_time:.2f}초")
        return self.vectorstore

    def load_vectorstore(self):
        """기존 벡터 DB 로드"""
        if not os.path.exists(self.persist_dir):
            raise FileNotFoundError(f"벡터 DB를 찾을 수 없습니다: {self.persist_dir}")

        print(f"\n📂 벡터 DB 로드 중...")

        self.vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )

        print(f"   ✅ 로드 완료")
        return self.vectorstore

    def get_retriever(self):
        """Retriever 반환 (검색용)"""
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다")

        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": Config.TOP_K}
        )


class DocumentIndexer:
    """문서 인덱싱 오케스트레이션"""

    def __init__(self):
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.embedding_manager = EmbeddingManager()
        self.db_manager = None

    def build_vectorstore(self):
        """
        벡터 DB 생성
        문서 로드 → 청킹 → 임베딩 → 벡터 DB 저장

        Returns:
            VectorStoreManager: 생성된 벡터 DB 관리자
        """
        print("\n📑 문서 인덱싱 시작...")

        # 문서 로드
        documents = self.loader.load_documents()
        if len(documents) == 0:
            print("❌ 문서를 로드할 수 없습니다")
            return None

        # 청킹
        chunks = self.chunker.chunk_documents(documents)

        # 임베딩 + 벡터 DB 생성
        embeddings = self.embedding_manager.get_embeddings()
        self.db_manager = VectorStoreManager(embeddings)
        self.db_manager.create_vectorstore(chunks)

        print(f"✅ 벡터 DB 생성 완료")
        return self.db_manager

    def get_or_create_vectorstore(self):
        """
        기존 벡터 DB가 있으면 로드, 없으면 생성

        Returns:
            VectorStoreManager: 벡터 DB 관리자
        """
        embeddings = self.embedding_manager.get_embeddings()
        db_manager = VectorStoreManager(embeddings)

        # 기존 벡터 DB 확인
        if os.path.exists(Config.CHROMA_DB_PATH):
            print(f"\n📂 기존 벡터 DB 발견")
            try:
                db_manager.load_vectorstore()
                print(f"✅ 기존 벡터 DB 로드 완료")
                return db_manager
            except Exception as e:
                print(f"⚠️  벡터 DB 로드 실패: {e}")
                print(f"   새로 생성합니다...")

        # 벡터 DB 생성
        self.db_manager = db_manager
        self.build_vectorstore()
        return self.db_manager
