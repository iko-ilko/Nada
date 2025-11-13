# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Multimodal RAG Beauty Coaching System** - A LangChain-based RAG (Retrieval-Augmented Generation) system that analyzes user face images combined with status descriptions to provide beauty coaching advice.

**Tech Stack:**
- LangChain (langchain-core, langchain-openai, langchain-community, langchain-text-splitters, langchain-huggingface)
- OpenAI APIs (GPT-4o-mini for vision/LLM, embeddings)
- Chroma (vector database)
- Python 3.8+

## Architecture Overview

### RAG Pipeline Architecture

The system implements a proper LangChain RAG pipeline with these stages:

```
DocumentLoader → TextChunker → EmbeddingManager → Chroma VectorDB
    ↓
Retriever (as_retriever()) → VisionAnalyzer (RAG pipeline) → MultimodalRAGChain
    ↓
Result: JSON analysis + metadata logging
```

### Core Components

1. **Document Processing Pipeline** (`src/loader.py`, `src/db.py`, `src/embedder.py`)
   - `DocumentLoader`: Loads PDF documents from `data/papers/`
   - `TextChunker`: Splits documents into 300-token chunks with 50-token overlap
   - `EmbeddingManager`: Uses `all-MiniLM-L12-v2` model for embeddings
   - `VectorStoreManager`: Manages Chroma vector database (`chroma_db/`)

2. **Retriever** (`src/db.py`)
   - Uses `vectorstore.as_retriever()` with similarity search
   - Returns Top-3 most relevant documents
   - Configured via `Config.TOP_K = 3`

3. **Vision & RAG Pipeline** (`src/vision.py`)
   - `VisionAnalyzer` class with injected `retriever`
   - `analyze_image_with_context()` implements RAG:
     1. `retriever.invoke(search_query)` - Document retrieval
     2. `_format_docs()` - Format search results as text
     3. `ChatOpenAI.invoke(messages)` - Multimodal LLM call with image + RAG context
     4. `_extract_json()` - Parse JSON from response

4. **Orchestration** (`src/rag.py`)
   - `MultimodalRAGChain` class coordinates the pipeline
   - Injects `retriever` into `VisionAnalyzer`
   - Extracts paper metadata and logs results via `AnalysisLogger`

5. **Configuration & Logging**
   - `src/config.py`: Centralized configuration (LLM settings, embedding model, image detail level)
   - `src/logger.py`: Saves analysis results + metadata to JSON in `logs/` directory

### Configuration

**Key Config Settings** (`src/config.py`):
- `LLM_MODEL = "gpt-4o-mini"` - Vision-capable LLM
- `LLM_TEMPERATURE = 0.3` - Low randomness for consistency
- `EMBEDDING_MODEL = "all-MiniLM-L12-v2"` - Lightweight embedding model
- `IMAGE_DETAIL = "low"` - Can be changed to "high" for detailed analysis
- `CHUNK_SIZE = 300`, `CHUNK_OVERLAP = 50` - Document chunking parameters
- `TOP_K = 3` - Number of documents to retrieve
- `CHROMA_DB_PATH = "./chroma_db"` - Vector database location
- `DATA_DIR = "./data/papers"` - Document directory

**Environment Variables** (`.env`):
- `OPEN_API_KEY` - OpenAI API key (required)

## Common Development Tasks

### Initial Setup

1. **Environment Setup**
   ```bash
   # Create .env file with:
   # OPEN_API_KEY=sk-...

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Vector Database Setup**
   ```bash
   python main.py
   # Responds to prompt:
   # "Do you want to reload documents and recreate vector DB? (y/n):"
   # Enter 'y' to create/recreate, 'n' to use existing
   ```

### Running the RAG Pipeline

```bash
# Full pipeline execution:
python main.py

# This will:
# 1. Load/create vector database
# 2. Initialize RAG components (embeddings, vectorstore, retriever)
# 3. Run test_multimodal_rag() with sample image and user state
# 4. Display results with retrieved papers and analysis
# 5. Save analysis to logs/analysis_TIMESTAMP.json
```

### Testing with Different Inputs

Modify `main.py` bottom section:
```python
if __name__ == "__main__":
    main()
    test_multimodal_rag(
        image_url="YOUR_IMAGE_URL",
        user_state="YOUR_STATUS_DESCRIPTION",
        image_detail="low"  # or "high"
    )
```

### Adding New Documents

1. Place PDF files in `data/papers/`
2. Run `main.py` and select 'y' to recreate vector database
3. Documents will be automatically loaded, chunked, embedded, and stored

### Checking Saved Analyses

```bash
# View latest analysis log
cat logs/analysis_*.json | python -m json.tool

# Each log contains:
# - timestamp
# - config settings used
# - retrieved papers (source, type, page, content preview)
# - LLM analysis result (JSON)
```

### Changing Image Detail Level

```python
# In main.py or direct usage:
test_multimodal_rag(image_detail="high")  # More detailed vision analysis (more expensive)
# or
test_multimodal_rag(image_detail="low")   # Quick analysis (cheaper)
```

## Critical Implementation Details

### Import Paths (LangChain Version-Specific)

The project uses latest LangChain packages. Import paths are carefully chosen:

```python
# ✅ Correct imports:
from langchain_community.document_loaders import PyPDFLoader  # PDF loading
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Chunking
from langchain_huggingface import HuggingFaceEmbeddings  # Embeddings
from langchain_community.vectorstores import Chroma  # Vector DB
from langchain_openai import ChatOpenAI  # LLM
from langchain_core.messages import SystemMessage, HumanMessage  # Messages

# ❌ Avoid old paths (will cause errors):
# from langchain.document_loaders import PyPDFLoader  # WRONG
# from langchain.text_splitter import RecursiveCharacterTextSplitter  # WRONG
# from langchain.embeddings import HuggingFaceEmbeddings  # WRONG
```

### Project Root Environment Variable

The project sets `PROJECT_ROOT` for proper .env loading:

```python
# main.py top section:
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ['PROJECT_ROOT'] = str(project_root)
```

This allows `src/config.py` to load `.env` from correct location.

### RAG Pipeline Flow in Vision Analyzer

The `VisionAnalyzer.analyze_image_with_context()` method implements the RAG pipeline:

```python
# 1️⃣ Document retrieval (uses passed retriever)
search_results = self.retriever.invoke(search_query)

# 2️⃣ Format documents for context
formatted_docs = self._format_docs(search_results)

# 3️⃣ Build multimodal message (image + text context)
messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content=[
        {"type": "image_url", "image_url": {"url": image_url, "detail": detail_level}},
        {"type": "text", "text": prompt_with_rag_context}
    ])
]

# 4️⃣ LLM processes image + retrieved documents
response = self.llm.invoke(messages)

# 5️⃣ Extract JSON analysis from response
analysis = self._extract_json(response.content)
```

**Key Point**: The `retriever` is injected into `VisionAnalyzer` via constructor. This allows the vision module to perform document retrieval as part of its pipeline.

### Output Structure

Each execution produces:

```
Console Output:
- RAG Pipeline Construction (steps 1-5)
- RAG Pipeline Execution
- Retrieved papers (rank, source, page, content preview)
- LLM analysis JSON result
- Log file location

logs/analysis_TIMESTAMP.json:
{
  "timestamp": "ISO timestamp",
  "metadata": {
    "config": {...},
    "image": {...},
    "input": {"user_state": "..."},
    "search": {
      "total_results": 3,
      "papers": [{...}, {...}, {...}]
    }
  },
  "analysis": {
    "Hair": {...},
    "Skin": {...},
    "Contour": {...}
  }
}
```

## Important Code Locations

- **Vector Database**: `chroma_db/` - Persistent Chroma database
- **Source Documents**: `data/papers/` - Input PDFs
- **Analysis Logs**: `logs/` - JSON results with metadata
- **System Prompt**: `src/prompt/response_ko.prt` - Loaded by test_multimodal_rag()
- **Main Entry Point**: `main.py:main()` - Vector DB setup, `test_multimodal_rag()` - Pipeline execution

## Debugging Tips

1. **Import Errors**: Check LangChain package versions. Use `pip list | grep langchain` to verify installed packages.

2. **Vector DB Issues**: Delete `chroma_db/` and run `main.py` to recreate.

3. **API Key Issues**: Verify `OPEN_API_KEY` in `.env` (note: not `OPENAI_API_KEY`, it's `OPEN_API_KEY`).

4. **Image Detail Level**: "high" is more expensive but gives better analysis. "low" is faster and cheaper.

5. **Retriever Not Finding Documents**: Ensure `data/papers/` contains PDFs and vector DB was properly created.

## LCEL (LangChain Expression Language) Implementation

### What is LCEL?

LCEL is a declarative way to compose LangChain components using the pipe operator (`|`). Benefits:
- **Composability**: Chain components with clean syntax
- **Streaming**: First-class streaming support
- **Observability**: Automatic logging to LangSmith
- **Async Support**: Built-in async/await support

### LCEL in This Project

The project uses proper LCEL syntax with the pipe operator:

```python
# LCEL Chain: retriever | format_docs
rag_chain = self.retriever | RunnableLambda(self._format_docs)

# Usage:
formatted_docs = rag_chain.invoke(search_query)
# This pipes: search_query → retriever → format_docs → formatted_docs
```

**Key Components:**
- **Retriever**: `vectorstore.as_retriever()` returns a Runnable
- **RunnableLambda**: Wraps Python function to make it Runnable
- **Pipe Operator |**: Connects components (calls `__or__` method)

### LCEL Pipeline Flow

```
Input (user_state)
    ↓
retriever.invoke(user_state)  # Runnable[str] → List[Document]
    ↓
RunnableLambda(format_docs)   # Runnable[List[Document]] → str
    ↓
Output (formatted_docs)
```

Equivalent to: `retriever | RunnableLambda(format_docs)`

## Key Decisions & Rationale

1. **LCEL for Composition**: Uses proper LCEL syntax with pipe operator instead of manual method chaining for clarity and composability.

2. **Proper RAG Pipeline**: Uses LangChain's `as_retriever()` for standard retrieval patterns.

3. **Retriever Injection**: `VisionAnalyzer` receives `retriever` in constructor, making dependencies explicit.

4. **RunnableLambda for Custom Logic**: Python functions wrapped with `RunnableLambda` to integrate with LCEL chains.

5. **Separate Vision Module**: RAG context and image analysis in `VisionAnalyzer`, keeping concerns separated.

6. **JSON Logging**: All analyses logged with full metadata for audit trail and reproducibility.

7. **Modular Configuration**: Single `Config` class for easy parameter adjustment without code changes.

8. **Multimodal Processing**: Image + RAG context processed together by LLM for better understanding.
