"""Chat endpoints with RAG-powered streaming."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.auth.dependencies import get_current_user, User, require_user
from app.rag.indexer import get_or_create_index
from app.rag.query import query_repository_stream

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    owner: str
    repo: str
    question: str


class IndexRequest(BaseModel):
    owner: str
    repo: str


@router.post("/index")
async def index_repo(
    request: IndexRequest,
    user: User = Depends(require_user),
):
    """
    Index a GitHub repository for the first time.
    This clones the repo, creates embeddings, and stores them.
    Only needs to be called once per repo.
    """
    try:
        collection_name = await get_or_create_index(
            request.owner, request.repo, user.id
        )
        return {
            "status": "success",
            "message": f"Repository {request.owner}/{request.repo} indexed successfully",
            "collection": collection_name,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/ask")
async def ask_question(
    request: ChatRequest,
    user: User = Depends(require_user),
):
    """
    Ask a question about an indexed repository.
    Streams the response token by token.
    
    First time using a repo? Call /api/chat/index first.
    """
    # Ensure the repo is indexed
    try:
        collection_name = await get_or_create_index(
            request.owner, request.repo, user.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to access repository: {str(e)}")

    # Stream the response
    async def generate():
        async for token in query_repository_stream(
            request.owner, request.repo, request.question
        ):
            yield token

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/repos")
async def list_indexed_repos():
    """
    List all currently indexed repositories.
    """
    from app.rag.indexer import CHROMA_DIR
    import os
    
    repos = []
    if CHROMA_DIR.exists():
        for folder in CHROMA_DIR.iterdir():
            if folder.is_dir():
                repos.append(folder.name.replace("_", "/", 1))
    
    return {"repos": repos}