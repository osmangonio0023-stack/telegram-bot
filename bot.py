from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8688397504:AAF8ffdb0okhUJlawf7WO-A7qJoGLz6jQvs"

keyboard = [
["💰 Balance","🎮 Quiz"],
["🎡 Spin","📋 Daily Task"],
["🏆 Leaderboard","👥 Referral"],
["💸 Withdraw"]
]

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Welcome to Earning Bot\n\nChoose an option:",
        reply_markup=reply_markup
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "💰 Balance":
        await update.message.reply_text("Your balance: 0 coins")

    elif text == "🎮 Quiz":
        await update.message.reply_text("Quiz coming soon")

    elif text == "🎡 Spin":
        await update.message.reply_text("Spin feature coming soon")

    elif text == "📋 Daily Task":
        await update.message.reply_text("Daily reward coming soon")

    elif text == "🏆 Leaderboard":
        await update.message.reply_text("Leaderboard coming soon")

    elif text == "👥 Referral":
        await update.message.reply_text("Referral system coming soon")

    elif text == "💸 Withdraw":
        await update.message.reply_text("Withdraw system coming soon")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buttons))

print("Bot Running...")

app.run_polling()