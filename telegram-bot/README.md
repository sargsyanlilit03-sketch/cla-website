# CLA Telegram Support Bot

An AI-powered Telegram support agent for Chess Logic Academy, built with Claude claude-sonnet-4-6 and python-telegram-bot.

## What it does

- Answers purchase & Gumroad questions (lost downloads, access issues, refunds)
- Answers chess content questions based on the 6 CLA guides
- Escalates unresolved issues to you via a private Telegram message

## Setup

### 1. Get your credentials

| Credential | Where to get it |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Message @BotFather → /newbot |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/ |
| `OWNER_TELEGRAM_ID` | Message @userinfobot — it replies with your numeric ID |

### 2. Install dependencies

```bash
cd telegram-bot
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your three values
```

### 4. Run the bot

```bash
python bot.py
```

The bot uses long-polling — it runs on your machine and checks Telegram for new messages every few seconds. Keep the terminal open while you want the bot live.

## Commands

| Command | What it does |
|---|---|
| `/start` | Greeting + menu |
| `/reset` | Clear conversation history (fresh start) |

## Escalation

When a user has an unresolved issue or asks for a human, Claude flags the conversation with `[ESCALATE: <summary>]`. The bot:
1. Strips the marker from the user-facing reply
2. Sends you a private alert message with the user's name, Telegram handle, ID, and issue summary

Make sure you've started a conversation with your bot at least once so Telegram allows it to message you.

## Customisation

- **System prompt / knowledge base** → [`knowledge.py`](knowledge.py)
- **Conversation memory length** → `MAX_HISTORY` in `bot.py` (default: 20 messages)
- **Claude model** → `model=` in `call_claude()` — swap to `claude-opus-4-7` for more complex reasoning
