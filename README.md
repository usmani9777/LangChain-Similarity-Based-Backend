# LangChain RAG API

A production-ready **Retrieval-Augmented Generation (RAG)** backend built with FastAPI, LangChain, ChromaDB, Redis, and MongoDB. The system supports three distinct RAG modes, a multi-layer memory architecture, LLM tool-calling, and background document ingestion.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Memory System](#memory-system)
- [RAG Modes](#rag-modes)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)

---

## Overview

This API allows users to chat with their documents using an LLM. It retrieves relevant context from a vector database (ChromaDB), combines it with personal memories (MongoDB) and recent chat history (Redis), and generates grounded, context-aware answers. The system can automatically classify and persist user-shared information (goals, personal facts, etc.) as long-term memories.

---

## Architecture

```
Client Request
     │
     ▼
Session Middleware ──── Assigns/reads session_id cookie
     │
     ▼
FastAPI Routers
 ├── /rag          ─── Document upload & ingestion
 ├── /user         ─── RAG query endpoints
 └── /Session      ─── In-session history endpoints
     │
     ▼
Services Layer
 ├── Rag.py              ─── Standard RAG pipeline
 ├── Rag_Tools.py        ─── Tool-enabled RAG pipeline
 ├── Agentic_rag.py      ─── Agentic orchestration loop
 ├── LongTermMemory.py   ─── Memory classification & retrieval
 └── memory_services.py  ─── Redis session history helpers
     │
     ▼
Storage Layer
 ├── ChromaDB          ─── Vector store (document chunks)
 ├── Redis             ─── In-session chat history
 └── MongoDB           ─── Long-term personal memories
```

---

## Features

- **Three RAG Modes**: Standard, Tool-Enabled, and fully Agentic with an orchestration loop
- **Multi-layer Memory**: In-session (Redis), long-term by type (MongoDB), and document knowledge (ChromaDB)
- **Automatic Memory Classification**: Uses spaCy NLP to detect and categorize user-shared information into `Personal`, `Goal`, or `Fact` types
- **LLM Tool Calling**: LangChain tools for retrieving and saving memories, called autonomously by the LLM
- **Background File Ingestion**: Upload `.txt` or `.pdf` files; indexing runs in the background without blocking the response
- **Session Management**: Automatic session ID generation and persistence via HTTP cookies
- **Structured LLM Output**: All LLM responses are parsed into a strict Pydantic `Response` schema via `PydanticOutputParser`
- **Singleton Dependencies**: LLM, vector store, Redis, and MongoDB clients are initialized once via `@lru_cache`

---

## Tech Stack

| Component          | Technology                          |
| ------------------ | ----------------------------------- |
| Web Framework      | FastAPI + Uvicorn                   |
| LLM Orchestration  | LangChain, LangChain-OpenAI         |
| Vector Store       | ChromaDB                            |
| Embeddings         | HuggingFace (sentence-transformers) |
| In-Session Memory  | Redis                               |
| Long-Term Memory   | MongoDB (PyMongo)                   |
| NLP Classification | spaCy (`en_core_web_sm`)            |
| PDF Parsing        | PyPDF (via LangChain)               |
| Config Management  | Pydantic Settings                   |

---

## Project Structure

```
├── main.py                        # FastAPI app entrypoint, middleware & router registration
├── core/
│   ├── config.py                  # Pydantic Settings loaded from .env
│   ├── dependecies.py             # Singleton factories (LLM, vector store, Redis, MongoDB)
│   ├── logging_config.py          # Logging setup
│   └── prompt.py                  # LangChain prompt templates (RAG, Agentic, Tool-enabled)
├── Routes/
│   ├── rag.py                     # Document upload & vector DB ingestion endpoints
│   ├── user.py                    # RAG query endpoints (3 modes)
│   └── Insession_memory.py        # Session history retrieval endpoints
├── Services/
│   ├── Rag.py                     # Standard RAG pipeline
│   ├── Rag_Tools.py               # Tool-enabled RAG pipeline
│   ├── Agentic_rag.py             # Agentic RAG with orchestration loop (RagOrchestrator class)
│   ├── agent_executor.py          # (Legacy agent executor, currently unused)
│   ├── LongTermMemory.py          # Memory type classification + MongoDB retrieval/creation
│   └── memory_services.py         # Redis chat history helpers + session_id dependency
├── models/
│   ├── Response.py                # Structured LLM output schema (Pydantic)
│   ├── Query_Payload.py           # RagRequest and RedisQuery request models
│   ├── rag_request.py             # RAGRequest_Endpoint (endpoint input model)
│   ├── LongMemory_Models.py       # Memory Pydantic model with importance scoring
│   └── Text_Upload.py             # Text upload request model
├── Middleware/
│   └── Session_Id.py              # HTTP middleware for session cookie management
├── utils/
│   ├── db.py                      # TextRAGVectorStore (ChromaDB wrapper)
│   ├── Insession_Memory.py        # RedisDictSessionStore (Redis session store wrapper)
│   ├── mongo_memory.py            # MongoMemoryStore (MongoDB wrapper)
│   ├── RuleBasedMemoryClassifier.py # spaCy-based memory type classifier
│   ├── convert_to_txt.py          # Saves raw text content to .txt files in Storage/
│   ├── File_check.py              # Unique filename generator to avoid overwrites
│   └── tools/
│       ├── __init__.py            # Exports ALL_TOOLS list
│       ├── Mongo_Tool.py          # LangChain tools: retrieve_memories, save_memory
│       ├── Mongo_tools_withRunable.py  # Runnable-based variants of memory tools
│       └── Addition.py            # Example math tool (add)
├── chroma_db/                     # Persisted ChromaDB vector store
└── Storage/                       # Uploaded document files
```

---

## API Endpoints

### Document Ingestion (`/rag`)

| Method | Path                           | Description                                                          |
| ------ | ------------------------------ | -------------------------------------------------------------------- |
| `POST` | `/rag/add-file_withBackground` | Upload a `.txt` or `.pdf` file; indexing runs as a background task   |
| `POST` | `/rag/convert-and-add`         | Accept raw text via JSON body, save as `.txt`, and index immediately |
| `GET`  | `/rag/Check-Files`             | Check if a file exists in the storage directory                      |

### RAG Query (`/user`)

| Method | Path                       | Description                                                                   |
| ------ | -------------------------- | ----------------------------------------------------------------------------- |
| `GET`  | `/user/info`               | Health check for the user route                                               |
| `POST` | `/user/prompt`             | Echo a question (test endpoint)                                               |
| `POST` | `/user/prompt/rag`         | **Standard RAG** — retrieve context + long-term memories → LLM                |
| `POST` | `/user/prompt/rag_tools`   | **Tool-Enabled RAG** — LLM can call `retrieve_memories` / `save_memory` tools |
| `POST` | `/user/prompt/Agentic_rag` | **Agentic RAG** — multi-step orchestration loop with autonomous tool calling  |

**Request body for all RAG query endpoints:**

```json
{
  "question": "What are my fitness goals?",
  "user_id": "user123"
}
```

**Response schema:**

```json
{
  "Status_Code": 200,
  "Saving": "Goal",
  "Question": "What are my fitness goals?",
  "Article": "Relevant document excerpt...",
  "Answer": "Based on your documents and memories..."
}
```

The `Saving` field indicates whether the LLM classified the interaction as containing a memory worth persisting (`Personal`, `Goal`, `Fact`, or `None`).

### Session History (`/Session`)

| Method | Path                           | Description                                        |
| ------ | ------------------------------ | -------------------------------------------------- |
| `POST` | `/Session/prompt/GetPrompts`   | Get the recent Q&A history for the current session |
| `POST` | `/Session/prompt/Get_All`      | Get all stored session data across all users       |
| `POST` | `/Session/prompt/Get_all_keys` | Get all active session keys in Redis               |

---

## Memory System

The system uses three layers of memory working together to produce contextual, personalized answers.

### 1. In-Session Memory (Redis)

- Stores the most recent Q&A pairs for each active session
- Keyed by `session_id` (from the HTTP cookie)
- TTL-based expiry (configurable via `REDIS_TTL_SECONDS`)
- Automatically appended after every RAG response via a background task
- Used to maintain conversational continuity within a session

### 2. Long-Term Memory (MongoDB)

- Stores user-specific memories that persist across sessions
- Each memory has a `memory_type`: `Personal`, `Goal`, or `Fact`
- MongoDB indexes on `user_id`, `memory_type`, and `importance`
- Memories are retrieved sorted by `importance` (descending) and limited to 5
- Pruning supported via `prune_memories(threshold)` to remove low-importance entries

#### Memory Importance Scoring

Importance is computed automatically when a `Memory` object is created:

- **Type weight**: `Goal = 1.0`, `Personal = 0.9`, `Fact = 0.6`
- **Time decay**: Older memories fade (decay over 365 days)
- **Access boost**: Recently accessed memories are ranked higher

### 3. Rule-Based Memory Classifier (spaCy)

Before querying MongoDB, every user input is passed through the `RuleBasedMemoryClassifier`:

| Memory Type | Trigger Patterns                                          |
| ----------- | --------------------------------------------------------- |
| `Goal`      | "i want", "i plan", "my goal", "i aim", "i will"          |
| `Personal`  | "i am", "i like", "i prefer", "i enjoy", "i love"         |
| `Fact`      | Named entity detection via spaCy (PERSON, GPE, ORG, DATE) |

If no pattern matches and no relevant entities are found, `None` is returned and no memory lookup or save occurs.

---

## RAG Modes

### Standard RAG (`/user/prompt/rag`)

1. Embed the question and retrieve top-k document chunks from ChromaDB
2. Classify memory intent and retrieve matching memories from MongoDB
3. Fetch recent Q&A pairs from Redis
4. Invoke the LLM with article context + memories + history
5. Parse structured `Response`; if memory-worthy, persist to MongoDB asynchronously

### Tool-Enabled RAG (`/user/prompt/rag_tools`)

Same as standard RAG but the LLM has access to LangChain tools:

- **`retrieve_memories(user_id, memory_type)`** — fetch memories from MongoDB
- **`save_memory(user_id, session_id, memory_type, text)`** — persist a new memory
- **`add(a, b)`** — basic addition tool (demo)

The LLM autonomously decides when to call these tools based on the system prompt instructions.

### Agentic RAG (`/user/prompt/Agentic_rag`)

Implements a full agent loop via `RagOrchestrator`:

1. Retrieves document context and chat history
2. Enters an **orchestration loop** (max 5 iterations):
   - Calls the LLM with tools bound
   - Executes any requested tool calls, injecting `user_id` and `session_id` automatically
   - Appends tool results back to the message history
   - Breaks when the LLM stops requesting tools
3. A final **synthesis phase** re-invokes the bare LLM to produce a clean, structured answer from all accumulated context

---

## Configuration

All configuration is loaded from a `.env` file via Pydantic Settings. Create a `.env` in the project root:

```env
# Vector Store
persist_directory=chroma_db
embedding_model=sentence-transformers/all-MiniLM-L6-v2
chunk_size=500
chunk_overlap=50
top_k=3
rebuild=True

# LLM
API_KEY=your_openai_compatible_api_key
BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini

# Redis
REDIS_URL=redis://localhost:6379
REDIS_TTL_SECONDS=3600
REDIS_KEY_PREFIX=Chat_Session

# MongoDB
MONGO_URL=mongodb://localhost:27017
mongo_db_name=rag_db
mongo_collection_name=memories
MAX_ITEMS=20

# Storage
STORAGE_DIR=Storage
```

---

## Running the Server

**Prerequisites:**

- Python 3.10+
- Redis instance running
- MongoDB instance running
- spaCy model: `python -m spacy download en_core_web_sm`

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Start the server:**

```bash
python main.py
```

Or with Uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`
