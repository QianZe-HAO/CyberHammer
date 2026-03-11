import uuid
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from rich.console import Console
from utils import print_message
from agent import agent


console = Console()


config: RunnableConfig = {"configurable": {"thread_id": uuid.uuid4()}}

# Track the number of messages already printed
printed_messages = 0

while True:
    try:
        # get user input and exit if needed
        user_input = console.input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            console.print("Goodbye!", style="bold yellow")
            break

        for step in agent.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="values",
        ):

            messages = step["messages"]

            for msg in messages[printed_messages:]:
                msg: BaseMessage
                print_message(console=console, msg=msg)

            printed_messages = len(messages)

    except KeyboardInterrupt:
        console.print("Goodbye!", style="bold blue")
        break
