from langchain_ollama import ChatOllama
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_community.tools import DuckDuckGoSearchResults
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

import uuid
# -----------------------------------------------
# create session id
thread_id = str(uuid.uuid4())
# -----------------------------------------------
# Define the state of the system
# This is the state that will be passed between the nodes of the graph


class State(TypedDict):
    messages: Annotated[list, add_messages]
    res: str


graph_builder = StateGraph(State)

# -----------------------------------------------
llm = ChatOllama(model="qwen2.5:3b")
search_engine = DuckDuckGoSearchResults()
llm_with_tools = llm.bind_tools([search_engine])

tool_node = ToolNode(tools=[search_engine])

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是Cyber Researcher，你可以是一个AI机器人，可以联网搜索回答问题。用中文回答所有的问题。",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ])


def researcher_bot(state: State):
    prompt = prompt_template.invoke(state)
    response = llm_with_tools.invoke(prompt)
    return {"messages": response}


graph_builder.add_node("Researcher", researcher_bot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges(
    "Researcher",
    tools_condition,
)
# Any time a tool is called, we return to the researcher_bot to decide the next step
graph_builder.add_edge("tools", "Researcher")
graph_builder.add_edge(
    START,
    "Researcher",
)
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# -----------------------------------------------


def get_chatbot_response(query: str, thread_id: str):
    res = graph.invoke(
        {"messages": [HumanMessage(query)]},
        {"configurable": {"thread_id": thread_id}},
    )
    return res


res = get_chatbot_response("我想知道关于中国今天的新闻，请帮我搜索一下", thread_id)
print(res)
