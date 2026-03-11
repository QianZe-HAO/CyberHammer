# main.telegram.py
import asyncio
import logging
import os
import uuid
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
from md2tgmd import escape
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from rich.console import Console
from agent import agent


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", None)


console = Console()  # For internal logging; output will go to Telegram


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    if "thread_id" not in context.user_data:
        context.user_data["thread_id"] = str(uuid.uuid4())
        print(
            f"New conversation thread created for user {update.effective_user.id}: {context.user_data['thread_id']}"
        )
    await update.message.reply_text(
        "Hello! I'm a research assistant. Send me any topic, and I'll analyze it deeply."
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command to reset user's conversation thread"""
    context.user_data.clear()
    context.user_data["thread_id"] = str(uuid.uuid4())
    print(
        f"Conversation context cleared and new thread assigned for user {update.effective_user.id}: {context.user_data['thread_id']}"
    )
    await update.message.reply_text("Your chat context has been cleared!")


async def agent_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user message and stream agent response"""
    user_id = update.effective_user.id
    user_message = update.message.text

    thread_id = context.user_data.get("thread_id")

    print(f"Processing message from user {user_id}")
    print(f"Using thread ID: {thread_id}")
    print(f"User message: {user_message}")

    if not thread_id:
        thread_id = str(uuid.uuid4())
        context.user_data["thread_id"] = thread_id
        print(f"Assigned new thread ID for user {user_id}: {thread_id}")

    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    thinking_msg = await update.message.reply_text("Thinking...")

    try:
        res = agent.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config=config,
        )
        ai_messages = [m for m in res["messages"] if m.type == "ai"]
        if ai_messages:
            last_response: BaseMessage = ai_messages[-1]
            content = escape(last_response.content)
            try:
                await thinking_msg.edit_text(content, parse_mode="MarkdownV2")
                print(
                    f"Successfully sent AI response (MarkdownV2) to user {user_id}")
            except Exception as e:
                print(
                    f"Markdown parsing failed for user {user_id}, falling back to plain text: {e}"
                )
                await thinking_msg.edit_text(content)
            console.print(last_response.content)
        else:
            await thinking_msg.edit_text("No AI response generated.")
            print(f"Agent returned no AI messages for user {user_id}")
    except Exception as e:
        logger.error(
            f"Error in agent processing for user {user_id}: {e}", exc_info=True
        )
        await thinking_msg.edit_text("An error occurred while processing your request.")


async def main():
    """Start the Telegram Bot with agent integration"""
    app_builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    if TELEGRAM_PROXY_URL:
        app_builder = app_builder.proxy(TELEGRAM_PROXY_URL).get_updates_proxy(
            TELEGRAM_PROXY_URL
        )
    application = app_builder.build()

    # Set bot commands
    await application.bot.set_my_commands(
        [
            ("start", "Start the bot"),
            ("clear", "Clear your conversation history"),
        ]
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, agent_response)
    )

    # Error handler
    application.add_error_handler(
        lambda update, ctx: logger.error(
            f"Update {update} caused error: {ctx.error}")
    )

    logger.info("Starting Telegram bot with DeepAgent...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
