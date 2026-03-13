import sqlite3
import random
import time
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

ADMIN_ID = 7950791526
CHANNEL = "@methodzone10"

# DATABASE
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance INTEGER DEFAULT 0,
referrer INTEGER,
ref_count INTEGER DEFAULT 0,
last_daily INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS withdraws(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount INTEGER,
method TEXT,
number TEXT,
status TEXT
)
""")

conn.commit()

# FUNCTIONS

def get_user(user):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user,))
    data = cur.fetchone()

    if not data:
        cur.execute("INSERT INTO users(user_id,balance) VALUES(?,0)", (user,))
        conn.commit()

def get_balance(user):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (user,))
    return cur.fetchone()[0]

def add_balance(user,amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount,user))
    conn.commit()

# KEYBOARD

keyboard = [
["💰 Balance","🎮 Quiz"],
["🎡 Spin","📋 Daily Task"],
["👥 Referral","🏆 Leaderboard"],
["💳 Withdraw"]
]

markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)

# START

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    get_user(user)

    if context.args:

        ref = int(context.args[0])

        if ref != user:

            cur.execute("SELECT referrer FROM users WHERE user_id=?", (user,))
            data = cur.fetchone()[0]

            if data is None:

                cur.execute("UPDATE users SET referrer=? WHERE user_id=?", (ref,user))
                cur.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id=?", (ref,))
                add_balance(ref,10)

                conn.commit()

    await update.message.reply_text(
        "🤖 Welcome to Earning Bot",
        reply_markup=markup
    )

# BALANCE

async def balance(update,context):

    bal = get_balance(update.effective_user.id)

    await update.message.reply_text(f"💰 Balance: {bal} coins")

# DAILY

async def daily(update,context):

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

async def spin(update,context):

    reward = random.choice([0,2,5,10,20])

    add_balance(update.effective_user.id,reward)

    await update.message.reply_text(f"🎡 You won {reward} coins")

# REFERRAL

async def referral(update,context):

    user = update.effective_user.id

    link = f"https://t.me/earning_task99_bot?start={user}"

    cur.execute("SELECT ref_count FROM users WHERE user_id=?", (user,))
    refs = cur.fetchone()[0]

    await update.message.reply_text(
        f"👥 Your referral link:\n{link}\n\nReferrals: {refs}"
    )

# LEADERBOARD

async def leaderboard(update,context):

    cur.execute("SELECT user_id,ref_count FROM users ORDER BY ref_count DESC LIMIT 10")

    rows = cur.fetchall()

    text = "🏆 Referral Leaderboard\n\n"

    rank = 1

    for r in rows:

        text += f"{rank}. {r[0]} - {r[1]} refs\n"

        rank += 1

    await update.message.reply_text(text)

# WITHDRAW

async def withdraw(update,context):

    user = update.effective_user.id

    bal = get_balance(user)

    if bal < 50:

        await update.message.reply_text("❌ Minimum withdraw 5000 coins")

        return

    context.user_data["withdraw"] = True

    await update.message.reply_text("Send Bkash/Nagad number")

async def withdraw_number(update,context):

    if context.user_data.get("withdraw"):

        number = update.message.text

        user = update.effective_user.id

        cur.execute(
            "INSERT INTO withdraws(user_id,amount,method,number,status) VALUES(?,?,?,?,?)",
            (user,50,"bkash",number,"pending")
        )

        add_balance(user,-50)

        conn.commit()

        await update.message.reply_text("✅ Withdraw request sent")

        context.user_data["withdraw"] = False

# ADMIN PANEL

async def withdraws(update,context):

    if update.effective_user.id != ADMIN_ID:
        return

    cur.execute("SELECT id,user_id,amount FROM withdraws WHERE status='pending'")

    rows = cur.fetchall()

    text = "💳 Pending Withdraws\n\n"

    for r in rows:

        text += f"ID:{r[0]} User:{r[1]} Amount:{r[2]}\n"

    await update.message.reply_text(text)

async def approve(update,context):

    if update.effective_user.id != ADMIN_ID:
        return

    wid = context.args[0]

    cur.execute("UPDATE withdraws SET status='approved' WHERE id=?", (wid,))
    conn.commit()

    await update.message.reply_text("Withdraw approved")

# BUTTONS

async def buttons(update,context):

    text = update.message.text

    if text == "💰 Balance":
        await balance(update,context)

    elif text == "📋 Daily Task":
        await daily(update,context)

    elif text == "🎡 Spin":
        await spin(update,context)

    elif text == "👥 Referral":
        await referral(update,context)

    elif text == "🏆 Leaderboard":
        await leaderboard(update,context)

    elif text == "💳 Withdraw":
        await withdraw(update,context)

    else:
        await withdraw_number(update,context)

# APP

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("withdraws",withdraws))
app.add_handler(CommandHandler("approve",approve))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,buttons))

print("Bot Running...")

app.run_polling()