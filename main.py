import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from commands import start, handle_action

load_dotenv()

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN_MAIN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_action))

    app.run_polling()

if __name__ == '__main__':
    main()
