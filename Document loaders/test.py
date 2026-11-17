from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size = 10,
    separator= "\n"
    chunk_overlap = 1,
)

loader = TextLoader("Document loaders/notes.txt")

data = loader.load()

chunks = splitter.split_documents(data)

print(len(chunks))