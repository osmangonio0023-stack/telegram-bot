import sqlite3
import random
import time
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")

ADMIN_ID = 7950791526
CHANNEL = "@methodzone10"

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance INTEGER DEFAULT 0,
last_daily INTEGER DEFAULT 0,
last_spin INTEGER DEFAULT 0
)
""")

conn.commit()

def get_user(user):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user,))
    data = cur.fetchone()

    if not data:
        cur.execute("INSERT INTO users(user_id) VALUES(?)",(user,))
        conn.commit()

def add_balance(user,amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount,user))
    conn.commit()

def get_balance(user):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (user,))
    return cur.fetchone()[0]

keyboard = [
["💰 Balance","🎮 Quiz"],
["🎡 Spin","📋 Daily"],
["🏆 Leaderboard","👥 Referral"]
]

markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def check_join(update,context):

    user = update.effective_user.id

    member = await context.bot.get_chat_member(CHANNEL,user)

    if member.status in ["member","administrator","creator"]:
        return True
    else:
        await update.message.reply_text(
            f"❌ Join our channel first\nhttps://t.me/methodzone10"
        )
        return False

async def start(update,context):

    if not await check_join(update,context):
        return

    user = update.effective_user.id

    get_user(user)

    await update.message.reply_text(
        "🤖 Welcome to Task Bot",
        reply_markup=markup
    )

async def balance(update,context):

    bal = get_balance(update.effective_user.id)

    await update.message.reply_text(f"💰 Balance: {bal} coins")

async def quiz(update,context):

    context.user_data["answer"]="10"

    await update.message.reply_text("❓ 5+5=?")

async def answer(update,context):

    if context.user_data.get("answer"):

        if update.message.text=="10":

            add_balance(update.effective_user.id,5)

            await update.message.reply_text("✅ Correct +5 coins")

        context.user_data["answer"]=None

async def daily(update,context):

    user = update.effective_user.id

    cur.execute("SELECT last_daily FROM users WHERE user_id=?", (user,))
    last = cur.fetchone()[0]

    now = int(time.time())

    if now-last < 86400:

        await update.message.reply_text("⏳ Daily already claimed")

    else:

        add_balance(user,10)

        cur.execute("UPDATE users SET last_daily=? WHERE user_id=?", (now,user))
        conn.commit()

        await update.message.reply_text("📋 +10 coins")

async def spin(update,context):

    user = update.effective_user.id

    cur.execute("SELECT last_spin FROM users WHERE user_id=?", (user,))
    last = cur.fetchone()[0]

    now = int(time.time())

    if now-last < 3600:

        await update.message.reply_text("⏳ Spin cooldown 1h")

    else:

        reward = random.choice([0,2,5,10,20])

        add_balance(user,reward)

        cur.execute("UPDATE users SET last_spin=? WHERE user_id=?", (now,user))
        conn.commit()

        await update.message.reply_text(f"🎡 You won {reward} coins")

async def leaderboard(update,context):

    cur.execute("SELECT user_id,balance FROM users ORDER BY balance DESC LIMIT 10")

    rows = cur.fetchall()

    text="🏆 Leaderboard\n\n"

    r=1

    for i in rows:

        text+=f"{r}. {i[0]} - {i[1]}\n"

        r+=1

    await update.message.reply_text(text)

async def referral(update,context):

    user = update.effective_user.id

    link = f"https://t.me/earning_task99_bot?start={user}"

    await update.message.reply_text(link)

async def users(update,context):

    if update.effective_user.id != ADMIN_ID:
        return

    cur.execute("SELECT COUNT(*) FROM users")

    total = cur.fetchone()[0]

    await update.message.reply_text(f"👥 Users: {total}")

async def stats(update,context):

    if update.effective_user.id != ADMIN_ID:
        return

    cur.execute("SELECT SUM(balance) FROM users")

    total = cur.fetchone()[0]

    await update.message.reply_text(f"💰 Total coins: {total}")

async def broadcast(update,context):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    cur.execute("SELECT user_id FROM users")

    rows = cur.fetchall()

    for r in rows:
        try:
            await context.bot.send_message(r[0],msg)
        except:
            pass

async def buttons(update,context):

    text = update.message.text

    if text=="💰 Balance":
        await balance(update,context)

    elif text=="🎮 Quiz":
        await quiz(update,context)

    elif text=="📋 Daily":
        await daily(update,context)

    elif text=="🎡 Spin":
        await spin(update,context)

    elif text=="🏆 Leaderboard":
        await leaderboard(update,context)

    elif text=="👥 Referral":
        await referral(update,context)

    else:
        await answer(update,context)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("users",users))
app.add_handler(CommandHandler("broadcast",broadcast))
app.add_handler(CommandHandler("stats",stats))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,buttons))

print("Bot Running")

app.run_polling()