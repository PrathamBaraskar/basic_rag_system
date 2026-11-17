from langchain_community.document_loaders import WebBaseLoader


url= "https://www.apple.com/in/macbook-pro/proled-xdr-display/"
loader = WebBaseLoader(url)

data = loader.load()

print(data[0].page_content)