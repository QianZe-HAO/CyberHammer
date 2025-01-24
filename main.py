from langchain_ollama import ChatOllama

model = ChatOllama(model="qwen2.5:3b")
res = model.invoke("Come up with 10 names for a song about parrots")
print(res)
