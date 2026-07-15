# RepoX - AI-Powered Code Repository Analysis

RepoX lets you chat with your code repositories using LLMs. It indexes your entire git history (commits, diffs, PRs, issues) and lets you ask questions in natural language, with answers grounded in your actual codebase.

## Architecture

┌─────────────────────────────────────────────────────────────┐
│ Frontend (Next.js) │
│ Chat UI + Repository Browser │
└──────────────────────┬──────────────────────────────────────┘
│ HTTP/SSE
┌──────────────────────▼──────────────────────────────────────┐
│ Backend (FastAPI + Python) │
│ │
│ ┌──────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│ │ Auth │ │ GitHub API │ │ RAG Pipeline │ │
│ │ Module │ │ Gateway │ │ (LangChain) │ │
│ │ │ │ │ │ │ │
│ │ OAuth 2.0│ │ • Repos │ │ • Document Loaders │ │
│ │ Sessions │ │ • Commits │ │ • Text Splitters │ │
│ │ Token │ │ • PRs │ │ • Embeddings │ │
│ │ Encrypt │ │ • Issues │ │ • Vector Store │ │
│ └──────────┘ └──────────────┘ └──────────────────────┘ │
│ │
└──────────────────────┬──────────────────────────────────────┘
│
┌──────────────────────▼──────────────────────────────────────┐
│ Storage │
│ ┌──────────────────┐ ┌─────────────────────────┐ │
│ │ PostgreSQL │ │ Chroma / pgvector │ │
│ │ (metadata, users)│ │ (embeddings) │ │
│ └──────────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
