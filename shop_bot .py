import telebot
import sqlite3

BOT_TOKEN = "8486873532:AAFceOdNA4r-EgLf_bdDNPKumcYbDrk1aDU"
ADMIN_ID = 6619552482

bot = telebot.TeleBot(BOT_TOKEN)

# ================= DATABASE =================
conn = sqlite3.connect("shop.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    name TEXT PRIMARY KEY,
    price INTEGER
)
""")

conn.commit()

# ================= FUNCTIONS =================
def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.from_user.id)
    bot.reply_to(
        message,
        "🛒 Shop Bot এ স্বাগতম!\n\n"
        "/products - প্রডাক্ট দেখুন\n"
        "/balance - ব্যালেন্স\n"
        "/recharge - রিচার্জ করুন"
    )

# ================= BALANCE =================
@bot.message_handler(commands=['balance'])
def balance(message):
    bal = get_balance(message.from_user.id)
    bot.reply_to(message, f"💰 আপনার ব্যালেন্স: {bal} টাকা")

# ================= PRODUCTS =================
@bot.message_handler(commands=['products'])
def products(message):
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    if not rows:
        bot.reply_to(message, "❌ কোনো প্রডাক্ট নেই")
        return

    text = "🛍 প্রডাক্ট লিস্ট:\n"
    for name, price in rows:
        text += f"{name} - {price} টাকা\n"

    text += "\nঅর্ডার করতে লিখুন:\n/buy ProductName"
    bot.send_message(message.chat.id, text)

# ================= BUY =================
@bot.message_handler(commands=['buy'])
def buy(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "ব্যবহার:\n/buy ProductName")
        return

    product = args[1]
    cursor.execute("SELECT price FROM products WHERE name=?", (product,))
    row = cursor.fetchone()

    if not row:
        bot.reply_to(message, "❌ প্রডাক্ট পাওয়া যায়নি")
        return

    price = row[0]
    balance = get_balance(message.from_user.id)

    if balance < price:
        bot.reply_to(message, "❌ ব্যালেন্স নাই!\n/recharge")
        return

    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE user_id=?",
        (price, message.from_user.id)
    )
    conn.commit()

    bot.reply_to(message, f"✅ অর্ডার সফল!\n{product} - {price} টাকা")

# ================= RECHARGE =================
@bot.message_handler(commands=['recharge'])
def recharge(message):
    bot.send_message(
        message.chat.id,
        "💳 রিচার্জ করুন:\n\n"
        "📱 bKash: 01XXXXXXXXX\n"
        "📱 Nagad: 01XXXXXXXXX\n\n"
        "পাঠানোর পর Txn ID পাঠান"
    )

# ================= TXN ID =================
@bot.message_handler(func=lambda m: m.text.lower().startswith("txn"))
def txn(message):
    bot.send_message(
        ADMIN_ID,
        f"💰 Recharge Request\n"
        f"User: {message.from_user.id}\n"
        f"Txn ID: {message.text}"
    )
    bot.reply_to(message, "⏳ Txn ID পাঠানো হয়েছে, অপেক্ষা করুন")

# ================= ADMIN =================
@bot.message_handler(commands=['addproduct'])
def add_product(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, name, price = message.text.split()
        cursor.execute("INSERT INTO products VALUES (?,?)", (name, int(price)))
        conn.commit()
        bot.reply_to(message, "✅ প্রডাক্ট অ্যাড হয়েছে")
    except:
        bot.reply_to(message, "ব্যবহার:\n/addproduct Name Price")

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, uid, amount = message.text.split()
        cursor.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?",
            (int(amount), int(uid))
        )
        conn.commit()
        bot.send_message(int(uid), f"✅ {amount} টাকা ব্যালেন্স যোগ হয়েছে")
    except:
        bot.reply_to(message, "ব্যবহার:\n/addbalance user_id amount")

# ================= RUN =================
bot.infinity_polling()