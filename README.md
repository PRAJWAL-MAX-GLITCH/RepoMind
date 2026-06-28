<div align="center">

<img src="https://img.shields.io/badge/RepoMind-Local%20AI%20Code%20Intelligence-3b82f6?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgZmlsbD0iIzNiODJmNiIvPjwvc3ZnPg==" alt="RepoMind Banner" />

# 🧠 RepoMind

### Local AI-Powered Code Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb?style=flat-square&logo=react)](https://reactjs.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-06b6d4?style=flat-square&logo=tailwindcss)](https://tailwindcss.com)
[![Vite](https://img.shields.io/badge/Vite-6-646cff?style=flat-square&logo=vite)](https://vitejs.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

**Index any local repository. Ask developer questions. Analyze architecture. Find risky files.**
**100% local. 100% private. No cloud required.**

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [API Reference](#-api-reference)
- [Frontend Pages](#-frontend-pages)
- [Configuration](#-configuration)
- [How It Works](#-how-it-works)
- [Screenshots](#-screenshots)

---

## 🔍 Overview

**RepoMind** is a local-first AI code intelligence platform designed for developers who want to deeply understand codebases — without sending their source code to any external service.

It combines a **RAG (Retrieval-Augmented Generation) pipeline** with a **FastAPI backend** and a **React dashboard** to let you:

- **Index** any local repository by path
- **Ask** natural language questions and get answers with exact file + line citations
- **Summarize** what a project does in a structured developer-friendly format
- **Analyze** the architecture: entry points, tech stack, modules, file categories
- **Find hotspots**: risky, complex, or security-sensitive files detected by heuristics

Everything runs entirely on your machine.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🔍 **Semantic Code Search** | Vector-based retrieval across all indexed files |
| 💬 **Developer Q&A** | Natural language questions answered with file path + line citations |
| 📋 **Repository Summary** | Auto-generated onboarding overview: what it does, tech stack, entry files |
| 🏗️ **Architecture Analysis** | Identifies modules, entry points, config/auth/DB/API/ML file groups |
| 🔥 **Hotspot Finder** | Flags high-risk files based on size, complexity, secrets, and keyword density |
| 📂 **Smart Indexing** | Language-aware chunking and embedding of source files |
| 🔒 **100% Local & Private** | No data leaves your machine — runs on any local LLM or Ollama |
| 🎨 **Premium Dark UI** | React + Tailwind dashboard with live API health indicator |

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RepoMind System                         │
│                                                             │
│   ┌──────────────┐         ┌──────────────────────────┐    │
│   │  React UI    │  HTTP   │     FastAPI Backend       │    │
│   │  (Vite :3000)│◄───────►│     (Uvicorn :8080)      │    │
│   └──────────────┘         └──────────┬───────────────┘    │
│                                        │                    │
│              ┌─────────────────────────┼──────────────┐    │
│              │                         │              │    │
│        ┌─────▼──────┐    ┌─────────────▼──┐  ┌──────▼──┐  │
│        │  Analyzers  │    │  RAG Pipeline  │  │ Vector  │  │
│        │  - Summary  │    │  - Indexing    │  │  Store  │  │
│        │  - Arch.    │    │  - Retrieval   │  │(Chroma) │  │
│        │  - Hotspot  │    │  - Query Svc   │  └─────────┘  │
│        └─────────────┘    └───────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. User provides a local repo path via the UI
2. Backend walks the directory, parses files with language-aware chunkers
3. Chunks are embedded and stored in a local vector store (ChromaDB)
4. On query, relevant chunks are retrieved via semantic search
5. A local LLM generates an answer using the retrieved context
6. The UI renders the answer with cited file paths and line ranges

---

## 📁 Project Structure

```
RepoMind/
├── 📄 README.md                    ← You are here
├── 📄 pyproject.toml               ← Python package & dependencies
├── 📄 settings.yaml                ← Main application configuration
├── 📄 settings-test.yaml           ← Test environment config
├── 📄 version.txt                  ← Current version
│
├── 🐍 repomind/                    ← Core Python backend package
│   ├── __init__.py
│   ├── main.py                     ← App entry point
│   ├── paths.py                    ← Filesystem path constants
│   ├── constants.py                ← Shared constants
│   ├── global_handler.py           ← Global error/event handling
│   │
│   ├── 📡 api/                     ← FastAPI routers & schemas
│   │   ├── repos/
│   │   │   ├── router.py           ← /repos/* endpoints
│   │   │   └── schemas.py          ← Pydantic request/response models
│   │   └── server/
│   │       ├── chat/               ← Chat & streaming endpoints
│   │       ├── health/             ← GET /health
│   │       ├── ingest/             ← File ingestion router
│   │       ├── models/             ← LLM model listing endpoints
│   │       └── utils/              ← Auth, callbacks, artifact helpers
│   │
│   ├── 🤖 analyzers/               ← Code intelligence modules
│   │   ├── architecture_analyzer.py ← Structural analysis
│   │   ├── hotspot_finder.py        ← Risk & complexity detection
│   │   ├── repository_summary.py    ← Onboarding summary generator
│   │   └── summarizer.py            ← LLM-based summarization
│   │
│   ├── 🔍 rag/                     ← Retrieval-Augmented Generation
│   │   ├── indexing_pipeline.py    ← Repo walk → chunk → embed → store
│   │   ├── retriever.py            ← Semantic similarity retrieval
│   │   ├── query_service.py        ← Answer generation with context
│   │   └── chunk/                  ← Chunking models & strategies
│   │
│   ├── 📦 ingestion/               ← File ingestion pipeline
│   │   └── ingest/
│   │       ├── ingest_component.py ← Core ingestion orchestrator
│   │       ├── ingest_service.py   ← Ingestion service layer
│   │       └── progress/           ← Progress tracking models
│   │
│   ├── 🧩 parsers/                 ← Language-specific file parsers
│   │   └── readers/                ← Document readers per format
│   │
│   ├── 🗄️ artifact_index/          ← Vector store abstraction layer
│   │   ├── base_artifact_index.py  ← Abstract base class
│   │   └── vector_artifact_index.py ← ChromaDB implementation
│   │
│   ├── ⚙️ core/                    ← App core: settings, launcher, DI
│   │   ├── launcher.py             ← FastAPI app factory & router mounting
│   │   └── settings/               ← Pydantic settings management
│   │
│   ├── 🧠 models/                  ← LLM & embedding model management
│   │   ├── llm/                    ← LLM client wrappers
│   │   ├── embedding/              ← Embedding model components
│   │   └── model_discovery/        ← Auto-discovery of available models
│   │
│   ├── 📊 vector_store/            ← ChromaDB vector store integration
│   ├── 🔗 services/                ← Shared service interfaces
│   ├── 💬 chat/                    ← Chat session models
│   ├── 📣 events/                  ← Event system (streaming, SSE)
│   └── 🛠️ utils/                   ← Utilities (concurrency, logging, etc.)
│
├── 🎨 repomind-ui/                 ← React frontend (Vite)
│   ├── index.html                  ← Entry HTML (Inter + JetBrains Mono fonts)
│   ├── vite.config.js              ← Vite config + Tailwind plugin + proxy
│   ├── package.json
│   └── src/
│       ├── main.jsx                ← React entry point
│       ├── App.jsx                 ← Router + context wiring
│       ├── index.css               ← Design system (tokens, utilities, components)
│       │
│       ├── services/
│       │   └── api.js              ← All API calls (fetch wrappers)
│       │
│       ├── context/
│       │   └── RepoContext.jsx     ← Global repo list (localStorage-persisted)
│       │
│       ├── components/
│       │   ├── Sidebar.jsx         ← Left nav with active state
│       │   ├── Header.jsx          ← Top bar + live API health dot
│       │   ├── PageLayout.jsx      ← Full-viewport layout wrapper
│       │   └── ui.jsx              ← All reusable UI primitives
│       │
│       └── pages/
│           ├── Dashboard.jsx       ← Landing: stats, quick actions, recent repos
│           ├── IndexRepo.jsx       ← Repo indexing form + report
│           ├── Query.jsx           ← Q&A with answer + source citations
│           ├── Summary.jsx         ← Dev onboarding summary
│           ├── Architecture.jsx    ← Architecture analysis dashboard
│           └── Hotspots.jsx        ← Risk file finder with priority filters
│
├── 🗂️ frontend/                    ← Legacy single-file HTML UI (backup)
│   └── index.html
│
└── 🔧 scripts/                     ← Utility scripts
```

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| **Web Framework** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| **Language** | Python 3.11+ |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) (fast pip replacement) |
| **RAG Framework** | LlamaIndex / custom pipeline |
| **Vector Store** | [ChromaDB](https://www.trychroma.com/) (local, persistent) |
| **Embeddings** | Configurable (Ollama / OpenAI-compatible) |
| **LLM** | Configurable (Ollama / OpenAI-compatible) |
| **Config** | Pydantic Settings + YAML |
| **DI Container** | [injector](https://injector.readthedocs.io/) |

### Frontend
| Layer | Technology |
|-------|-----------|
| **Framework** | [React 18](https://react.dev/) (JavaScript, no TypeScript) |
| **Build Tool** | [Vite 6](https://vitejs.dev/) |
| **Styling** | [Tailwind CSS v4](https://tailwindcss.com/) |
| **Routing** | [React Router DOM v6](https://reactrouter.com/) |
| **Icons** | [Lucide React](https://lucide.dev/) |
| **Fonts** | Inter + JetBrains Mono (Google Fonts) |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm**
- **uv** (Python package manager) — `pip install uv`
- A running **LLM** (Ollama recommended, or any OpenAI-compatible API)

### Backend Setup

**1. Clone the repository**
```bash
git clone https://github.com/PRAJWAL-MAX-GLITCH/RepoMind.git
cd RepoMind
```

**2. Install Python dependencies**
```bash
pip install uv
uv sync
```

**3. Configure your LLM**

Edit `settings.yaml` to point to your model provider:

```yaml
# For Ollama (recommended for local use)
llm:
  mode: ollama
  ollama:
    llm_model: llama3.2
    embedding_model: nomic-embed-text
    api_base: http://localhost:11434

# For OpenAI-compatible API
llm:
  mode: openai
  openai:
    api_key: your-api-key
    model: gpt-4o-mini
```

**4. Start the backend server**
```bash
python -m repomind serve
```

The API will be available at **http://localhost:8080**
Swagger docs at **http://localhost:8080/docs**

---

### Frontend Setup

**1. Navigate to the frontend folder**
```bash
cd repomind-ui
```

**2. Install dependencies**
```bash
npm install
```

**3. Start the development server**
```bash
npm run dev
```

The UI will be available at **http://localhost:3000**

> The Vite dev server automatically proxies all `/repos/*` and `/health` requests to the backend at `:8080` — no CORS configuration needed.

---

## 📡 API Reference

All endpoints are prefixed with `/repos`. Full interactive docs at `http://localhost:8080/docs`.

### `POST /repos/index`
Index a local repository into the vector store.

**Request:**
```json
{
  "repo_path": "D:/Projects/my-repo"
}
```

**Response:**
```json
{
  "repo_name": "my-repo",
  "files_indexed": ["src/main.py", "src/utils.py"],
  "chunks_created": 142,
  "skipped_files": ["node_modules/...", ".git/..."],
  "languages_detected": ["Python", "YAML", "Markdown"],
  "index_location": ".local_data/..."
}
```

---

### `POST /repos/query`
Ask a semantic question about an indexed repository.

**Request:**
```json
{
  "repo_name": "my-repo",
  "question": "How does the authentication middleware work?",
  "top_k": 5
}
```

**Response:**
```json
{
  "repo_name": "my-repo",
  "question": "How does the authentication middleware work?",
  "answer": "Authentication is handled in src/auth/middleware.py (L12-L45). The middleware...",
  "source_chunks": [
    {
      "file_path": "src/auth/middleware.py",
      "file_name": "middleware.py",
      "language": "python",
      "start_line": 12,
      "end_line": 45,
      "chunk_type": "function",
      "symbol_name": "authenticate_request",
      "content": "def authenticate_request(request: Request):\n    ..."
    }
  ]
}
```

---

### `GET /repos/{repo_name}/summary`
Generate a developer onboarding summary.

**Query params:** `?repo_path=/absolute/path` (optional, for richer analysis)

**Response:**
```json
{
  "repo_name": "my-repo",
  "what_it_does": "A FastAPI backend for managing user authentication and...",
  "major_modules": ["auth", "api", "database", "utils"],
  "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
  "entry_files": ["main.py", "app/core/launcher.py"],
  "important_files": {
    "auth": ["app/auth/middleware.py", "app/auth/jwt.py"],
    "database": ["app/db/session.py", "app/models/user.py"],
    "api": ["app/api/v1/router.py"],
    "ml": [],
    "config": ["settings.yaml", ".env.example"]
  },
  "needs_review": ["app/utils/legacy_crypto.py"],
  "architecture_notes": "Follows a layered architecture with clear separation..."
}
```

---

### `GET /repos/{repo_name}/architecture`
Structural architecture analysis of the repository.

**Response:**
```json
{
  "repo_name": "my-repo",
  "project_summary": "A REST API service built with FastAPI...",
  "languages": ["Python", "SQL", "YAML"],
  "main_modules": ["auth", "api", "core", "models", "utils"],
  "entry_points": ["main.py", "app/__main__.py"],
  "important_files": {
    "auth": ["middleware.py", "jwt_handler.py"],
    "database": ["session.py", "base_model.py"],
    "api": ["router.py", "endpoints/users.py"],
    "config": ["settings.yaml"],
    "ml": [],
    "tests": ["tests/test_auth.py"]
  },
  "architecture_notes": ["Follows dependency injection pattern", "Uses alembic for migrations"]
}
```

---

### `GET /repos/{repo_name}/hotspots`
Identify risky, complex, or security-sensitive files.

**Response:**
```json
{
  "repo_name": "my-repo",
  "hotspots": [
    {
      "file_path": "app/auth/crypto.py",
      "reason": "Contains hardcoded secret patterns and high complexity score",
      "priority": "high",
      "category": "security"
    },
    {
      "file_path": "app/db/session.py",
      "reason": "Database connection file — central dependency for all services",
      "priority": "medium",
      "category": "database"
    }
  ]
}
```

---

### `GET /health`
Backend health check.

```json
{ "status": "ok" }
```

---

## 🖥️ Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| **Dashboard** | `/` | Overview with stats, quick action cards, and recently indexed repos |
| **Index Repository** | `/index-repo` | Path input form, indexing progress, and detailed report |
| **Ask Repo** | `/query` | Q&A with answer panel and source chunk citations |
| **Summary** | `/summary` | Structured developer onboarding summary per repository |
| **Architecture** | `/architecture` | File categories, tech stack, entry points, design notes |
| **Hotspots** | `/hotspots` | Priority-filtered list of risky or complex files |

---

## ⚙️ Configuration

The primary config file is `settings.yaml`. Key sections:

```yaml
server:
  port: 8080
  host: 0.0.0.0
  cors:
    enabled: true

llm:
  mode: ollama          # ollama | openai | mock
  ollama:
    llm_model: llama3.2
    embedding_model: nomic-embed-text
    api_base: http://localhost:11434

rag:
  chunk_size: 512
  chunk_overlap: 64
  similarity_top_k: 5

storage:
  local:
    data_path: local_data

embedding:
  mode: ollama
```

---

## 🔬 How It Works

### 1. Indexing Pipeline (`repomind/rag/indexing_pipeline.py`)
```
Repository Path
    │
    ▼
Directory Walk (recursive, respects .gitignore patterns)
    │
    ▼
Language-Aware Chunking (Python → AST-based, others → sliding window)
    │
    ▼
Metadata Attachment (file_path, language, start_line, end_line, symbol_name)
    │
    ▼
Embedding Generation (via configured embedding model)
    │
    ▼
ChromaDB Storage (namespaced by repo_name)
```

### 2. Query Pipeline (`repomind/rag/query_service.py`)
```
User Question + Repo Name
    │
    ▼
Embedding of Query
    │
    ▼
Semantic Retrieval (top-K chunks from ChromaDB, filtered by repo_name)
    │
    ▼
Context Assembly (chunks formatted with file path + line range)
    │
    ▼
LLM Prompt Construction (system prompt enforces citation format)
    │
    ▼
Answer Generation
    │
    ▼
Response: { answer, source_chunks[] }
```

### 3. Hotspot Detection (`repomind/analyzers/hotspot_finder.py`)
Files are scored by:
- **Centrality**: How often is this file retrieved across queries?
- **Keyword density**: Auth / secret / password / token / hardcoded patterns
- **File size & complexity**: Large files get flagged as maintenance risks
- **File category**: DB connections, auth handlers, API routers score higher
- **Pattern matching**: Regex for hardcoded credentials, TODO density

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with ❤️ by [Prajwal](https://github.com/PRAJWAL-MAX-GLITCH)

**RepoMind** — _Understand any codebase in minutes, not weeks._

</div>
