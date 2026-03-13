from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_db():
    return sqlite3.connect("bot.db")

@app.route("/")
def dashboard():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT SUM(balance) FROM users")
    coins = cur.fetchone()[0]

    cur.execute("SELECT user_id,balance FROM users ORDER BY balance DESC LIMIT 10")
    leaderboard = cur.fetchall()

    return render_template(
        "dashboard.html",
        users=users,
        coins=coins,
        leaderboard=leaderboard
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)