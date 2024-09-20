from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from db_utils import update_balance, get_balance

WAITING_FOR_INPUT = range(1)

def add_credits(ID, ammount):
    update_balance(ID, ammount)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id != 1417095779:
        print(user_id)
        await update.message.reply_text("You don't have permission to add credits.")
        return
    await update.message.reply_text("Enter ID and amount of credits:")
    return WAITING_FOR_INPUT

async def get_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ID, ammount = update.message.text.split()
        add_credits(int(ID), int(ammount))
        await update.message.reply_text(f"Successfully added {ammount} credits to ID {ID}. Current balance is: {get_balance(ID)}")
    except ValueError:
        await update.message.reply_text("Please enter the data in the format 'ID amount' (both should be integers).")
    return ConversationHandler.END  

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token('7426141098:AAEYFKY5f50vQexLQibGbXzfc0UpDeTvRw8').build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            WAITING_FOR_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

