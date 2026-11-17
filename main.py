from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from langchain_mistralai import MistralAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

embedding_model = MistralAIEmbeddings(
    model = "mistral-embed"
)

vectorstore = Chroma(
    persist_directory="chroma_db",
    embedding_function= embedding_model
)

retriever = vectorstore.as_retriever(
    search_type = "mmr",
    search_kwargs = {
        "k":4, #kitne retrieve karne hai !!!!
        "fetch_k": 10,  #pehele similarity search lagega then 10 milega usme mmr use hoga and usmese 4 select hoga
        "lambda_mult" :0.5   #value will be between 0 and 1 if the value is zero means very diverse result and 1 means less diverse results 
    }
)

model = ChatOpenRouter(model = "auto")

#prompt template 

prompt = ChatPromptTemplate.from_messages([
    ("system",
     """ you are a helpful ai assistant.
     use only the provided context to answer the question.
     
     if the answer is not present in the context, say: "I could not find the answer in the document." """),
     ("human", """ Context: {context}
     Question : {question}""")
])

print('Rag Started')
print('Press 0 to exit')

while True:
    query = input('you: ')
    if query == '0':
        break
    docs = retriever.invoke(query)

    context = "\n\n".join([
        doc.page_content for doc in docs
    ])

    final_prompt = prompt.invoke({
        "context" : context,
        "question" : query
    })

    response = model.invoke(final_prompt)

    print(f"\n AI : {response.content}")
