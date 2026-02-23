from langchain_core.messages import BaseMessage
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown


def print_message(console, msg: BaseMessage):

    role = msg.type.capitalize()
    content = msg.content
    if role == "Human":
        panel_title = Text("User", style="bold yellow")
        color = "green"
    elif role == "Ai":
        panel_title = Text("Assistant", style="bold magenta")
        color = "cyan"
    elif role == "Tool":
        panel_title = Text("Tool Call", style="bold blue")
        color = "blue"
    else:
        panel_title = Text(role, style="bold")
        color = "white"

    console.print(Panel(Markdown(content), title=panel_title, border_style=color))
