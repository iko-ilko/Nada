from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import re
import json
import time
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
    
    return text.strip()


def load_documents():
    loader = DirectoryLoader(
        "hairdata/",
        glob="**/*.pdf",
        loader_cls=PyPDFLoader
    )
    documents = loader.load()
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)
    return documents


def chunk_doc(documents, chunk_size=500, chunk_overlap=50):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
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
    documents = load_documents()
    chunked_documents = chunk_doc(documents)
    save_documents(chunked_documents, 'tmp.jsonl')

    print("=" * 50)
    print("임베딩 시작...")
    embedding_start = time.time()

    embeddings = OllamaEmbeddings(
        model="llama3",
    )
    vectorstore = Chroma.from_documents(
        documents=chunked_documents,
        embedding=embeddings,
        persist_directory="./chroma_db"  # 저장 경로
    )

    embedding_end = time.time()
    print(f"임베딩 완료: {embedding_end - embedding_start:.2f}초")
    print("=" * 50)

    retriever = vectorstore.as_retriever(
        search_type="similarity",  # 또는 "mmr"
        search_kwargs={"k": 3}  # 상위 3개 문서 검색
    )

    # llama3 모델 사용 (텍스트 전용)
    llm = ChatOllama(model="llama3")

    # 프롬프트 템플릿 생성
    template = """당신은 다음 3명의 전문가가 통합된 고급 이미지·뷰티 코칭 AI입니다.
- 1. 헤어 스타일리스트: 헤어 형태, 볼륨, 질감, 스타일 방향성, 머릿결 관리 등 분석
- 2. 피부 관리 전문가: 피부 톤, 수분·유분 상태, 결, 잡티, 광택 등 관찰
- 3. 얼굴 윤곽 디자이너: 눈·코·입 비율, 턱선, 볼살, 이마 곡선, 대칭, 입체감 등 분석

[분석 방식 지침]
1. 사용자가 제공한 성별, 직업, 상황 설명을 기반으로 한다.
2. 관찰은 반드시 시각적·감각적 요소 중 최소 3가지 이상을 활용하고 디테일을 풍부하게 묘사하여, 독자가 장면을 그릴 수 있게 작성한다.
3. 부정적인 표현을 피하고 개선 가능성을 중심으로 서술한다.
4. 개선 팁은 오늘 실천 가능한 구체적 행동이나 셀프 케어 방법만 포함해야 하며, 추상적 조언은 금지된다.
5. 따뜻하고 격려적인 어조를 유지하며, 객관적이되 전문적으로 작성한다.
6. 전문 용어를 적절히 사용하되 이해하기 쉬운 표현으로 설명한다.

[분석 카테고리]
1. 헤어(Hair)
2. 피부(Skin)
3. 윤곽(Contour)

[Output JSON Example]
{{
  "Appearance_Coaching": {{
    "Hair": {{
      "status": "헤어의 현재 상태에 대한 간결한 요약 설명",
      "improvement_tips": [
        "오늘 실천 가능한 구체적인 행동 1",
        "오늘 실천 가능한 구체적인 행동 2"
      ]
    }},
    "Skin": {{
      "status": "피부의 현재 상태에 대한 간결한 요약 설명",
      "improvement_tips": [
        "오늘 실천 가능한 구체적인 행동 1",
        "오늘 실천 가능한 구체적인 행동 2"
      ]
    }},
    "Contour": {{
      "status": "윤곽의 현재 상태에 대한 간결한 요약 설명",
      "improvement_tips": [
        "오늘 실천 가능한 구체적인 행동 1",
        "오늘 실천 가능한 구체적인 행동 2"
      ]
    }}
  }}
}}

출력은 반드시 위 JSON 형식으로 하며,
개선 팁은 반드시 오늘 실천 가능한 구체적 행동으로 작성하세요.
{context}

질문: {question}
답변:"""

    prompt = ChatPromptTemplate.from_template(template)

    # LCEL 방식으로 체인 구성
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # 사용 예시
    query = "화사해보이고 싶은데 염색 추천해줘"

    print("\n" + "=" * 50)
    print("RAG 쿼리 시작...")
    invoke_start = time.time()

    result = qa_chain.invoke(query)

    invoke_end = time.time()
    print(f"RAG 쿼리 완료: {invoke_end - invoke_start:.2f}초")
    print("=" * 50)

    print("\n답변:", result)

    print("\n참고 문서:")
    retrieved_docs = retriever.invoke(query)
    for doc in retrieved_docs:
        print(doc.page_content)

if __name__ == "__main__":
    main()