"""
벡터 DB 모듈
청킹, 임베딩, 벡터 DB 저장/로드를 담당합니다.
"""
import os
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from src.config import Config


class TextChunker:
    """문서 청킹"""

    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or Config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP

    def chunk_documents(self, documents):
        """
        문서를 작은 청크로 분할
        """
        print(f"\n🔪 문서 청킹 중...")
        print(f"   청크 크기: {self.chunk_size} 토큰")
        print(f"   오버랩: {self.chunk_overlap} 토큰")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = splitter.split_documents(documents)
        print(f"✅ 청킹 완료: {len(chunks)}개 청크 생성")
        return chunks


class VectorStoreManager:
    """벡터 DB 관리"""

    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.persist_dir = Config.CHROMA_DB_PATH
        self.collection_name = "papers"
        self.vectorstore = None

    def create_vectorstore(self, chunks):
        """
        청크들을 임베딩하고 벡터 DB에 저장
        """
        print(f"\n💾 벡터 DB에 저장 중...")
        print(f"   저장 위치: {self.persist_dir}")
        print(f"   청크 개수: {len(chunks)}개")

        start_time = time.time()

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_dir,
            collection_name=self.collection_name
        )

        elapsed_time = time.time() - start_time

        print(f"✅ 벡터 DB 저장 완료!")
        print(f"   소요 시간: {elapsed_time:.2f}초")
        return self.vectorstore

    def load_vectorstore(self):
        """
        기존 벡터 DB 로드
        """
        if not os.path.exists(self.persist_dir):
            raise FileNotFoundError(f"벡터 DB를 찾을 수 없습니다: {self.persist_dir}")

        print(f"\n📂 벡터 DB 로드 중: {self.persist_dir}")

        self.vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )

        print(f"✅ 벡터 DB 로드 완료")
        return self.vectorstore

    def get_vectorstore_or_create(self, chunks):
        """
        기존 벡터 DB가 있으면 로드, 없으면 새로 생성
        """
        if os.path.exists(self.persist_dir):
            print(f"📂 기존 벡터 DB 발견")
            return self.load_vectorstore()
        else:
            print(f"✨ 새로운 벡터 DB 생성")
            return self.create_vectorstore(chunks)

    def get_retriever(self):
        """
        Retriever 반환 (검색용)
        """
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다")

        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": Config.TOP_K}
        )
