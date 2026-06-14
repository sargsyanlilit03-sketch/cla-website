import os
import logging
import re
from collections import defaultdict
from dotenv import load_dotenv
import anthropic
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from knowledge import SYSTEM_PROMPT

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OWNER_TELEGRAM_ID = int(os.environ["OWNER_TELEGRAM_ID"])

MAX_HISTORY = 20  # messages per user (10 turns)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# In-memory conversation history keyed by Telegram user_id
histories: dict[int, list[dict]] = defaultdict(list)


def trim_history(history: list[dict]) -> list[dict]:
    """Keep the last MAX_HISTORY messages."""
    return history[-MAX_HISTORY:]


async def send_escalation(context: ContextTypes.DEFAULT_TYPE, user: object, summary: str) -> None:
    """Forward an escalation alert to the owner."""
    name = user.full_name or "Unknown"
    username = f"@{user.username}" if user.username else "no username"
    uid = user.id
    text = (
        f"🚨 CLA Support Escalation\n\n"
        f"User: {name} ({username})\n"
        f"ID: {uid}\n\n"
        f"Issue: {summary}"
    )
    try:
        await context.bot.send_message(chat_id=OWNER_TELEGRAM_ID, text=text)
    except Exception as e:
        logger.error("Failed to send escalation to owner: %s", e)


def call_claude(history: list[dict]) -> str:
    """Call Claude with the full conversation history and return the reply."""
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=history,
    )
    return response.content[0].text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome = (
        f"Hi {user.first_name}! 👋 Welcome to Chess Logic Academy support.\n\n"
        "I can help you with:\n"
        "• Accessing your guides after purchase\n"
        "• Questions about chess rules and concepts\n"
        "• Anything covered in the 6 CLA guides\n\n"
        "What can I help you with today?"
    )
    await update.message.reply_text(welcome)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    histories[update.effective_user.id].clear()
    await update.message.reply_text("Conversation reset. How can I help you?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    uid = user.id
    text = update.message.text.strip()

    if not text:
        return

    # Append user message to history
    histories[uid].append({"role": "user", "content": text})
    histories[uid] = trim_history(histories[uid])

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = call_claude(histories[uid])
    except Exception as e:
        logger.error("Claude API error: %s", e)
        await update.message.reply_text(
            "Sorry, I'm having trouble right now. Please try again in a moment."
        )
        return

    # Check for escalation signal
    escalation_match = re.search(r"\[ESCALATE:\s*(.+?)\]", reply, re.IGNORECASE | re.DOTALL)
    if escalation_match:
        summary = escalation_match.group(1).strip()
        await send_escalation(context, user, summary)
        # Remove the marker from the user-facing reply
        reply = re.sub(r"\[ESCALATE:\s*.+?\]", "", reply, flags=re.IGNORECASE | re.DOTALL).strip()

    # Append assistant reply to history
    histories[uid].append({"role": "assistant", "content": reply})
    histories[uid] = trim_history(histories[uid])

    await update.message.reply_text(reply)


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("CLA support bot starting (polling mode)…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
