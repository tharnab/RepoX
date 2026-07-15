"""Index a GitHub repository into the vector store."""

import os
from pathlib import Path
from git import Repo
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.auth.models import get_token_for_user

DATA_DIR = Path("./data/repos")
CHROMA_DIR = Path("./data/chroma")
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

embeddings = OllamaEmbeddings(model="all-minilm")


def get_repo_path(owner: str, repo: str) -> Path:
    return DATA_DIR / f"{owner}_{repo}"


async def clone_or_pull_repo(owner: str, repo: str, access_token: str) -> Path:
    repo_path = get_repo_path(owner, repo)
    clone_url = f"https://x-access-token:{access_token}@github.com/{owner}/{repo}.git"

    if repo_path.exists():
        git_repo = Repo(repo_path)
        origin = git_repo.remotes.origin
        origin.pull()
    else:
        Repo.clone_from(clone_url, repo_path)

    return repo_path


def load_commit_history(repo_path: Path, max_commits: int = 100) -> list:
    """Load recent commits as documents."""
    documents = []
    git_repo = Repo(repo_path)

    try:
        commits = list(git_repo.iter_commits("HEAD", max_count=max_commits))
    except Exception:
        return documents

    for commit in commits:
        if commit.parents:
            diffs = commit.parents[0].diff(commit)
            changed_files = []
            for diff in diffs:
                path = diff.b_path or diff.a_path
                change_type = "modified" if diff.a_path and diff.b_path else "added" if diff.new_file else "deleted"
                changed_files.append(f"  - {change_type}: {path}")
        else:
            changed_files = ["  - Initial commit"]

        content = f"""Commit: {commit.hexsha[:8]}
Author: {commit.author.name} <{commit.author.email}>
Date: {commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')}
Message: {commit.message.strip()}

Changed files:
{chr(10).join(changed_files[:20])}"""

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": f"commit:{commit.hexsha[:8]}",
                    "type": "commit",
                    "author": str(commit.author),
                    "date": commit.committed_datetime.isoformat(),
                    "repo": str(repo_path.name),
                },
            )
        )

    return documents


def load_repo_files(repo_path: Path) -> list:
    """Load code files as Documents."""
    documents = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
    skip_extensions = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".exe"}
    max_files = 200

    file_count = 0
    for file_path in repo_path.rglob("*"):
        if file_count >= max_files:
            break
        if file_path.is_file():
            if any(skip in file_path.parts for skip in skip_dirs):
                continue
            if file_path.suffix.lower() in skip_extensions:
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.strip() and len(content) < 5000:
                    relative_path = file_path.relative_to(repo_path)
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={
                                "source": str(relative_path),
                                "type": "code",
                                "repo": str(repo_path.name),
                            },
                        )
                    )
                    file_count += 1
            except (UnicodeDecodeError, PermissionError):
                continue
    return documents


def index_repository(owner: str, repo: str, repo_path: Path) -> str:
    """Index both code files and commit history."""
    collection_name = f"{owner}_{repo}"

    print(f"📂 Loading files from {repo_path}...")
    code_docs = load_repo_files(repo_path)
    print(f"✅ Loaded {len(code_docs)} files")

    print(f"📝 Loading commit history...")
    commit_docs = load_commit_history(repo_path)
    print(f"✅ Loaded {len(commit_docs)} commits")

    all_docs = code_docs + commit_docs

    if not all_docs:
        raise ValueError(f"No content found in {owner}/{repo}")

    print(f"✂️ Splitting into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    code_chunks = text_splitter.split_documents(code_docs)
    all_chunks = code_chunks + commit_docs
    print(f"✅ Created {len(all_chunks)} chunks")

    # Create embeddings in smaller batches
    print(f"🧠 Creating embeddings in batches...")
    batch_size = 20
    vectorstore = None
    
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        print(f"   Processing batch {i//batch_size + 1}/{(len(all_chunks) + batch_size - 1)//batch_size}...")
        
        try:
            if vectorstore is None:
                vectorstore = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    collection_name=collection_name,
                    persist_directory=str(CHROMA_DIR),
                )
            else:
                vectorstore.add_documents(batch)
        except Exception as e:
            print(f"❌ Error on batch: {e}")
            raise
    
    print(f"✅ Indexing complete! {len(all_chunks)} chunks indexed")

    return collection_name

async def get_or_create_index(owner: str, repo: str, user_id: int) -> str:
    collection_name = f"{owner}_{repo}"
    chroma_path = CHROMA_DIR / collection_name

    if chroma_path.exists() and any(chroma_path.iterdir()):
        return collection_name

    token = await get_token_for_user(user_id)
    if not token:
        raise ValueError("GitHub token not found. Please sign in again.")

    repo_path = await clone_or_pull_repo(owner, repo, token)
    return index_repository(owner, repo, repo_path)