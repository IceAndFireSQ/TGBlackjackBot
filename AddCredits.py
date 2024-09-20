import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from db_utils import update_balance, get_balance

load_dotenv()

WAITING_FOR_INPUT = range(1)

def add_credits(user_id, amount):
    update_balance(user_id, amount)


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if str(user_id) != os.getenv("ADMIN1"):
        print(f"Unauthorized user attempted to add credits: {user_id}")
        await update.message.reply_text("You don't have permission to add credits.")
        return ConversationHandler.END

    await update.message.reply_text("Enter the user ID and amount of credits to add (e.g., '12345678 100'):")
    return WAITING_FOR_INPUT


async def get_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id, amount = update.message.text.split()
        user_id = int(user_id)
        amount = int(amount)
        add_credits(user_id, amount)
        current_balance = get_balance(user_id)
        await update.message.reply_text(
            f"Successfully added {amount} credits to user ID {user_id}.\nCurrent balance: {current_balance:.2f}"
        )
    except ValueError:
        await update.message.reply_text(
            "Invalid format. Please enter the data in the format 'ID amount' (both should be integers)."
        )
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN_PAY')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN_PAY not found in environment variables")

    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            WAITING_FOR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == '__main__':
    main()
