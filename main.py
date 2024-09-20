import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from commands import start, menu, balance, play, hit, stand, double, split

load_dotenv()

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN_MAIN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("hit", hit))
    app.add_handler(CommandHandler("stand", stand))
    app.add_handler(CommandHandler("double", double))
    app.add_handler(CommandHandler("split", split))

    app.run_polling()

if __name__ == '__main__':
    main()
