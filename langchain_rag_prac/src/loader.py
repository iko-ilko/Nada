"""
문서 로드 모듈
PDF와 TXT 파일을 로드하고 메타데이터를 추가합니다.
"""
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from src.config import Config


class DocumentLoader:
    """문서 로더"""

    def __init__(self, folder_path=None):
        self.folder_path = folder_path or Config.DATA_DIR

    def load_documents(self):
        """
        폴더 안의 모든 PDF와 TXT 파일을 로드
        """
        documents = []

        if not os.path.exists(self.folder_path):
            print(f"❌ 폴더를 찾을 수 없습니다: {self.folder_path}")
            return documents

        # 폴더 안의 모든 파일 찾기
        pdf_files = list(Path(self.folder_path).glob("*.pdf"))
        txt_files = list(Path(self.folder_path).glob("*.txt"))

        print(f"\n📂 {self.folder_path} 에서 파일 찾는 중...")
        print(f"   PDF 파일: {len(pdf_files)}개")
        print(f"   TXT 파일: {len(txt_files)}개")

        if len(pdf_files) == 0 and len(txt_files) == 0:
            print("⚠️  문서가 없습니다!")
            print(f"   {self.folder_path} 에 PDF 또는 TXT 파일을 넣어주세요")
            return documents

        # PDF 파일 로드
        print("\n📄 PDF 파일 로드 중...")
        for pdf_file in pdf_files:
            try:
                print(f"   로딩: {pdf_file.name}...", end=" ")
                loader = PyPDFLoader(str(pdf_file))
                docs = loader.load()

                # 메타데이터 추가 (출처 추적용)
                for doc in docs:
                    doc.metadata["source"] = pdf_file.name
                    doc.metadata["type"] = "pdf"

                documents.extend(docs)
                print(f"✅ ({len(docs)} 페이지)")
            except Exception as e:
                print(f"❌ 오류: {e}")

        # TXT 파일 로드
        print("\n📝 TXT 파일 로드 중...")
        for txt_file in txt_files:
            try:
                print(f"   로딩: {txt_file.name}...", end=" ")
                loader = TextLoader(str(txt_file), encoding="utf-8")
                docs = loader.load()

                # 메타데이터 추가
                for doc in docs:
                    doc.metadata["source"] = txt_file.name
                    doc.metadata["type"] = "txt"

                documents.extend(docs)
                print(f"✅")
            except Exception as e:
                print(f"❌ 오류: {e}")

        total_pages = len(documents)
        print(f"\n✅ 총 {len(pdf_files) + len(txt_files)}개 파일에서 {total_pages}개 문서 로드 완료")
        return documents
