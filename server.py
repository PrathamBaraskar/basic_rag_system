import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

app = FastAPI(title="Nexus RAG API", version="1.0.0")

# Ensure directories exist
os.makedirs("chroma_db", exist_ok=True)
os.makedirs("Document loaders", exist_ok=True)

# Initialize RAG components
embedding_model = MistralAIEmbeddings(model="mistral-embed")
vectorstore = Chroma(
    persist_directory="chroma_db",
    embedding_function=embedding_model
)

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "fetch_k": 10, "lambda_mult": 0.5}
)

model = ChatOpenRouter(model="auto")

prompt = ChatPromptTemplate.from_messages([
    ("system",
     """you are a helpful ai assistant.
     use only the provided context to answer the question.

     if the answer is not present in the context, say: "I could not find the answer in the document." """),
    ("human", """ Context: {context}
     Question : {question}""")
])

class QueryRequest(BaseModel):
    question: str
    k: Optional[int] = 4
    lambda_mult: Optional[float] = 0.5

@app.get("/", response_class=HTMLResponse)
async def read_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Nexus RAG UI not found. Please ensure index.html is present.</h1>"

@app.get("/app.js")
async def get_js():
    return FileResponse("app.js", media_type="application/javascript")

@app.get("/api/documents")
async def list_documents():
    # List PDFs in Document loaders folder
    docs_folder = "Document loaders"
    files = []
    if os.path.exists(docs_folder):
        for f in os.listdir(docs_folder):
            if f.endswith(".pdf"):
                path = os.path.join(docs_folder, f)
                size_mb = f"{os.path.getsize(path) / (1024*1024):.1f} MB"
                files.append({
                    "id": f,
                    "name": f,
                    "size": size_mb,
                    "chunks": 42,
                    "status": "indexed"
                })
    return {"documents": files}

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join("Document loaders", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process and index PDF into ChromaDB
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)

        vectorstore.add_documents(chunks)
        vectorstore.persist()

        return {
            "success": True,
            "filename": file.filename,
            "chunks": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _extract_text_content(content):
    """Extract text from various LangChain response content formats."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Handle list of content blocks (e.g., [{"type": "text", "text": "..."}])
        texts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                texts.append(block["text"])
            elif isinstance(block, str):
                texts.append(block)
        return "".join(texts)
    return str(content)

@app.post("/api/query")
async def query_rag(req: QueryRequest):
    try:
        # Update retriever kwargs if provided
        retriever.search_kwargs["k"] = req.k
        retriever.search_kwargs["lambda_mult"] = req.lambda_mult

        docs = retriever.invoke(req.question)
        context = "\n\n".join([doc.page_content for doc in docs])

        final_prompt = prompt.invoke({
            "context": context,
            "question": req.question
        })

        response = model.invoke(final_prompt)

        # Safely extract text content from response
        answer_text = _extract_text_content(response.content)

        sources = []
        for doc in docs:
            source_name = os.path.basename(doc.metadata.get("source", "Document.pdf"))
            page = doc.metadata.get("page", 1) + 1
            sources.append({
                "title": source_name,
                "page": page,
                "snippet": doc.page_content[:150] + "..."
            })

        return {
            "answer": answer_text,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Nexus RAG Server at http://localhost:8000")
    print("📁 Open index.html directly in your browser or visit http://localhost:8000")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
