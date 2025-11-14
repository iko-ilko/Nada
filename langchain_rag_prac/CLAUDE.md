# CLAUDE.md

Guidance for working on this multimodal RAG beauty coaching system.

## Working Principles

When analyzing or modifying code in this repository:

1. **Understand the actual flow** - Read and trace through the code, understand what it actually does (not what it's supposed to do)
2. **Objective analysis** - Ask "why is this here?" and "is this necessary?" Don't assume it's correct
3. **Avoid over-engineering** - Simple, working code is better than complex, theoretical code
4. **One problem at a time** - Solve concrete issues, not hypothetical ones

## Project Overview

**Multimodal RAG Beauty Coaching System** - Analyzes user face images combined with status descriptions to provide personalized beauty coaching using RAG (Retrieval-Augmented Generation).

**Core Flow:**
```
User Input (image + status)
    ↓
RAG Search (status → retrieve relevant documents)
    ↓
Multimodal LLM (image + documents → analysis)
    ↓
Result (JSON coaching advice)
```

## Current Architecture

### File Structure
```
src/
├─ config.py           - Configuration (models, paths, parameters)
├─ indexer.py          - Document indexing (loader + chunker + embeddings + vectorstore)
├─ vision.py           - Image analysis with RAG context
├─ rag.py              - Orchestration layer
└─ logger.py           - Result logging

main.py                - Entry point
```

### Component Overview

- **config.py**: Configuration and settings
- **indexer.py**: Document indexing (initialization only)
- **vision.py**: Image analysis
- **rag.py**: Orchestration layer
- **logger.py**: Result logging

### Key Data Flow

```
main()
  └─ setup_vectorstore()
     └─ DocumentIndexer.get_or_create_vectorstore()
        └─ (load docs → chunk → embed → create DB)

  └─ MultimodalRAGChain(retriever)
     └─ query_with_image_and_state(image_url, user_state, system_prompt)
        └─ VisionAnalyzer.analyze_image_with_context()
           ├─ retriever.invoke(user_state) → search_results
           ├─ _format_docs(search_results) → formatted_text
           ├─ _build_lcel_chain(system_prompt) → chain object
           ├─ chain.invoke({image_url, user_state, formatted_docs})
           └─ return {analysis, search_results, ...}
```

## Key Concepts

**RAG Search:**
- Query: user_state (not image context)
- Purpose: Retrieve relevant documents to supplement image analysis
- Integration: Retrieved documents + image processed together by LLM

**Multimodal Processing:**
- Image + RAG context combined in single LLM call
- LLM receives both visual and textual information for analysis

## Setup & Execution

```bash
python main.py
```

Initial run will prompt to create/recreate vector database.
