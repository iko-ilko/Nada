from langchain_community.document_loaders import PyPDFLoader
# from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import re
import json
load_dotenv()


def clean_text(text):
    """텍스트 공백 정리"""
    text = re.sub(r' {2,}', ' ', text)
    
    text = text.replace('\t', ' ')
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    lines = [line for line in text.split('\n') if line]
    text = '\n'.join(lines)
    
    text = re.sub(r'법제처\s+\d+\s+국가법령정보센터', '', text)
    
    text = re.sub(r'고용노동부\s*\([^)]+\)\s*\d{2,3}-\d{2,4}-\d{4}', '', text)
    
    return text.strip()


def load_documents():
    loader = PyPDFLoader("sample.pdf")
    documents = loader.load()
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)
    return documents


def chunk_doc(documents, chunk_size=500, chunk_overlap=50):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", "", r"\n제\d+조", r"\n제\d+장",],
        keep_separator=True 
    )
    splits = text_splitter.split_documents(documents)
    return splits


def save_documents(documents, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, page in enumerate(documents):
            data = {
                'page': i + 1,
                'text': page.page_content,
                'metadata': {
                    'source': 'sample.pdf',
                    'page': page.metadata.get('page', i)
                }
            }
            f.write(json.dumps(data, ensure_ascii=False) + '\n')


def main():
    text = input("무엇을 도와드릴까요? : ")
    documents = load_documents()
    chunked_documents = chunk_doc(documents)
    save_documents(chunked_documents, 'tmp.jsonl')
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
    )
    vector = embeddings.embed_query(text)
    print(vector[:5])
    # print(f"임베딩 차원: {len(embedded_query)}")
    # embedded_docs = embeddings.embed_documents(chunked_documents)
    # print(f"문서 개수: {len(embedded_docs)}")

if __name__ == "__main__":
    main()