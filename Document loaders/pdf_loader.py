from langchain_community.document_loaders import PyPDFLoader

from langchain_text_splitters import TokenTextSplitter

data = PyPDFLoader("C:/Generative AI Projects/RAG/Document loaders/Atomic Habits Tiny Changes, Remarkable Results (James Clear) (z-library.sk, 1lib.sk, z-lib.sk).pdf")

docs = data.load()

splitter = TokenTextSplitter(
    chunk_size = 10000,
    chunk_overlap = 1
)

chunks = splitter.split_documents(docs)


print(chunks[0].page_content)