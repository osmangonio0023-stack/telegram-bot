import sqlite3
import random
import time
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")

# DATABASE
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance INTEGER DEFAULT 0,
last_daily INTEGER DEFAULT 0
)
""")

conn.commit()

# FUNCTIONS

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    data = cur.fetchone()

    if not data:
        cur.execute("INSERT INTO users(user_id,balance) VALUES(?,0)", (user_id,))
        conn.commit()

def get_balance(user_id):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()[0]

def add_balance(user_id, amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount,user_id))
    conn.commit()

# BUTTONS

keyboard = [
["💰 Balance","🎮 Quiz"],
["🎡 Spin","📋 Daily Task"],
["🏆 Leaderboard","👥 Referral"],
["💸 Withdraw"]
]

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# START

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    get_user(user)

    await update.message.reply_text(
        "🤖 Welcome to Earning Bot",
        reply_markup=reply_markup
    )

# BALANCE

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bal = get_balance(update.effective_user.id)
    await update.message.reply_text(f"💰 Balance: {bal} coins")

# QUIZ

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["answer"] = "10"
    await update.message.reply_text("❓ 5 + 5 = ?")

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("answer"):

        if update.message.text == context.user_data["answer"]:
            add_balance(update.effective_user.id,5)
            context.user_data["answer"] = None

            await update.message.reply_text("✅ Correct! +5 coins")

        else:
            await update.message.reply_text("❌ Wrong answer")

# DAILY

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    cur.execute("SELECT last_daily FROM users WHERE user_id=?", (user,))
    last = cur.fetchone()[0]

    now = int(time.time())

    if now - last < 86400:
        await update.message.reply_text("⏳ Come back tomorrow")

    else:
        add_balance(user,10)

        cur.execute("UPDATE users SET last_daily=? WHERE user_id=?", (now,user))
        conn.commit()

        await update.message.reply_text("✅ Daily reward +10 coins")

# SPIN

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    reward = random.choice([0,2,5,10,20])

    add_balance(update.effective_user.id,reward)

    await update.message.reply_text(f"🎡 You won {reward} coins")

# LEADERBOARD

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    cur.execute("SELECT user_id,balance FROM users ORDER BY balance DESC LIMIT 10")

    rows = cur.fetchall()

    text = "🏆 Leaderboard\n\n"

    rank = 1

    for r in rows:
        text += f"{rank}. {r[0]} - {r[1]} coins\n"
        rank += 1

    await update.message.reply_text(text)

# REFERRAL

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    link = f"https://t.me/earning_task99_bot?start={user}"

    await update.message.reply_text(f"👥 Referral link:\n{link}")

# WITHDRAW

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):

    bal = get_balance(update.effective_user.id)

    if bal < 50:
        await update.message.reply_text("❌ Minimum withdraw 50 coins")

    else:
        add_balance(update.effective_user.id,-50)

        await update.message.reply_text("💸 Withdraw request sent")

# BUTTON HANDLER

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "💰 Balance":
        await balance(update,context)

    elif text == "🎮 Quiz":
        await quiz(update,context)

    elif text == "📋 Daily Task":
        await daily(update,context)

    elif text == "🎡 Spin":
        await spin(update,context)

    elif text == "🏆 Leaderboard":
        await leaderboard(update,context)

    elif text == "👥 Referral":
        await referral(update,context)

    elif text == "💸 Withdraw":
        await withdraw(update,context)

    else:
        await answer(update,context)

# APP

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,buttons))

print("Bot Running...")

app.run_polling()