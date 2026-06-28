<div align="center">

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
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [API Reference](#-api-reference)
- [Frontend Pages](#-frontend-pages)
- [How It Works](#-how-it-works)

---

## 🔍 Overview

**RepoMind** is a local-first AI code intelligence platform designed for developers who want to deeply understand codebases — without sending their source code to any external service.

It combines a **RAG (Retrieval-Augmented Generation) pipeline** with a **FastAPI backend** and a **React dashboard** to let you:

- **Index** any local repository by path
- **Ask** natural language questions and get answers with exact file + line citations
- **Summarize** what a project does in a structured developer-friendly format
- **Analyze** the architecture — entry points, tech stack, modules, file categories
- **Find hotspots** — risky, complex, or security-sensitive files detected by heuristics

Everything runs entirely on your machine.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🔍 **Semantic Code Search** | Vector-based retrieval across all indexed files |
| 💬 **Developer Q&A** | Natural language questions answered with file path + line citations |
| 📋 **Repository Summary** | Auto-generated onboarding overview — what it does, tech stack, entry files |
| 🏗️ **Architecture Analysis** | Identifies modules, entry points, config/auth/DB/API/ML file groups |
| 🔥 **Hotspot Finder** | Flags high-risk files based on size, complexity, secrets, and keyword density |
| 📂 **Smart Indexing** | Language-aware chunking and embedding of source files |
| 🔒 **100% Local & Private** | No data leaves your machine — runs on any local LLM or Ollama |
| 🎨 **Premium Dark UI** | React + Tailwind dashboard with live API health indicator |

---

## 📁 Project Structure

```
RepoMind/
│
├── repomind/                    ← Core Python backend package
│   ├── api/
│   │   ├── repos/               ← /repos/* API endpoints and schemas
│   │   └── server/              ← Chat, health, ingest, models routers
│   │
│   ├── analyzers/               ← Code intelligence modules
│   │   ├── architecture_analyzer.py
│   │   ├── hotspot_finder.py
│   │   ├── repository_summary.py
│   │   └── summarizer.py
│   │
│   ├── rag/                     ← RAG pipeline (indexing + retrieval + query)
│   │   ├── indexing_pipeline.py
│   │   ├── retriever.py
│   │   └── query_service.py
│   │
│   ├── ingestion/               ← File ingestion and chunking pipeline
│   ├── parsers/                 ← Language-specific file readers
│   ├── artifact_index/          ← ChromaDB vector store abstraction
│   ├── core/                    ← App factory, settings, dependency injection
│   ├── models/                  ← LLM and embedding model management
│   ├── vector_store/            ← Vector store integration layer
│   └── utils/                   ← Shared utilities
│
├── repomind-ui/                 ← React frontend (Vite + Tailwind)
│   └── src/
│       ├── components/          ← Sidebar, Header, PageLayout, UI primitives
│       ├── pages/               ← Dashboard, IndexRepo, Query, Summary, Architecture, Hotspots
│       ├── services/api.js      ← All API fetch calls
│       └── context/             ← Global repo state (localStorage)
│
├── settings.yaml                ← Main application configuration
├── pyproject.toml               ← Python dependencies
└── README.md
```

---

## 🛠️ Tech Stack

### Backend

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI + Uvicorn |
| Language | Python 3.11+ |
| Package Manager | uv |
| RAG Framework | LlamaIndex |
| Vector Store | ChromaDB (local, persistent) |
| Embeddings | Configurable — Ollama or OpenAI-compatible |
| LLM | Configurable — Ollama or OpenAI-compatible |
| Config | Pydantic Settings + YAML |

### Frontend

| Layer | Technology |
|-------|-----------|
| Framework | React 18 (JavaScript) |
| Build Tool | Vite 6 |
| Styling | Tailwind CSS v4 |
| Routing | React Router DOM v6 |
| Icons | Lucide React |
| Fonts | Inter + JetBrains Mono |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- uv — install with `pip install uv`
- A running LLM (Ollama recommended, or any OpenAI-compatible API)

---

### Backend Setup

**Step 1 — Clone the repository**

```
git clone https://github.com/PRAJWAL-MAX-GLITCH/RepoMind.git
cd RepoMind
```

**Step 2 — Install Python dependencies**

```
pip install uv
uv sync
```

**Step 3 — Configure your LLM**

Open `settings.yaml` and set your model provider. For local use, Ollama with `llama3.2` and `nomic-embed-text` is recommended.

**Step 4 — Start the backend**

```
python -m repomind serve
```

- API runs at **http://localhost:8080**
- Swagger docs at **http://localhost:8080/docs**

---

### Frontend Setup

**Step 1 — Go to the frontend folder**

```
cd repomind-ui
```

**Step 2 — Install dependencies**

```
npm install
```

**Step 3 — Start the dev server**

```
npm run dev
```

- UI runs at **http://localhost:3000**
- Vite automatically proxies all `/repos/*` requests to the backend — no extra config needed.

---

## 📡 API Reference

All endpoints are prefixed with `/repos`. Full interactive docs at `http://localhost:8080/docs`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/repos/index` | Index a local repository into the vector store |
| `POST` | `/repos/query` | Ask a natural language question about an indexed repo |
| `GET` | `/repos/{repo_name}/summary` | Generate a developer onboarding summary |
| `GET` | `/repos/{repo_name}/architecture` | Run structural architecture analysis |
| `GET` | `/repos/{repo_name}/hotspots` | Find risky or complex files by heuristics |
| `GET` | `/health` | Backend health check |

### Endpoint Details

**POST /repos/index**
Accepts an absolute local path. Walks the directory, chunks all source files by language, embeds them, and stores in ChromaDB. Returns a report with files indexed, skipped files, languages detected, and total chunks created.

**POST /repos/query**
Accepts a repo name, a natural language question, and an optional top-K value. Retrieves the most relevant code chunks semantically and generates an answer using the LLM. Returns the answer text along with source chunks that include file paths and line ranges.

**GET /repos/{repo_name}/summary**
Returns a structured developer summary covering what the project does, its major modules, tech stack, entry files, important file groups (auth, DB, API, ML, config), files needing review, and architecture notes. Pass `?repo_path=` for richer analysis.

**GET /repos/{repo_name}/architecture**
Returns a structural breakdown including detected languages, main modules, entry points, and categorized important files (auth, DB, API, config, ML, tests). Also includes key architectural observations.

**GET /repos/{repo_name}/hotspots**
Scores files by risk using heuristics — file size, secret patterns, keyword density (auth/db/token/password), and centrality in retrieval. Returns a list of flagged files with reason and priority (high / medium / low).

---

## 🖥️ Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Overview with stats, quick action cards, and recently indexed repos |
| Index Repository | `/index-repo` | Path input form, indexing progress, and detailed report |
| Ask Repo | `/query` | Q&A with answer panel and source chunk citations |
| Summary | `/summary` | Structured developer onboarding summary per repository |
| Architecture | `/architecture` | File categories, tech stack, entry points, design notes |
| Hotspots | `/hotspots` | Priority-filtered list of risky or complex files |

---

## 🔬 How It Works

### Indexing Pipeline

When you provide a repository path, RepoMind recursively walks the directory and skips irrelevant files (node_modules, .git, binaries). Each source file is split into chunks using language-aware strategies — Python files use AST-based splitting, others use a sliding window approach. Each chunk is tagged with its file path, language, start and end line numbers, and symbol name if applicable. The chunks are then embedded using the configured embedding model and stored in ChromaDB under a namespace for that repository.

### Query Pipeline

When you ask a question, it is first embedded using the same model. ChromaDB performs a vector similarity search filtered by the repository namespace and returns the top-K most relevant chunks. These chunks are assembled into a context block with file path and line range annotations. The LLM receives this context along with your question and generates a precise, cited answer. The response includes both the answer text and the source chunks so the UI can display file paths and line numbers.

### Hotspot Detection

Each file in the repository is scored across multiple dimensions — its size and complexity, density of technical debt markers (TODO, FIXME, HACK), presence of patterns matching hardcoded secrets or credentials, and whether it belongs to a category known to be sensitive (auth handlers, database connections, API routers). Files are then ranked and grouped into high, medium, and low priority buckets.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch — `git checkout -b feature/my-feature`
3. Commit your changes — `git commit -m 'feat: add my feature'`
4. Push to the branch — `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built by [Prajwal](https://github.com/PRAJWAL-MAX-GLITCH)

**RepoMind** — Understand any codebase in minutes, not weeks.

</div>
