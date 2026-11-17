from langchain_community.vectorstores import Chroma
from langchain_mistralai import MistralAIEmbeddings
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
load_dotenv()

loader = PyPDFLoader("Document loaders/Zema_Global_Data_Corporation-Data_analyst_resume.pdf")

docs = loader.load()

embedding_model = MistralAIEmbeddings(
    model="mistral-embed"
)

vectorstore = Chroma.from_documents(
    documents = docs,
    embedding = embedding_model,
    persist_directory= "chroma_db"
)

result = vectorstore.similarity_search("tell me about pratham",k=2)

for r in result:
    print(r)