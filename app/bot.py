import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
ADMIN_ID_2 = 6514315888
ADMIN_IDS = [ADMIN_CHAT_ID, ADMIN_ID_2]

DB_FILE = Path(__file__).parent / "userdb.json"
PROOFS_DIR = Path(__file__).parent / "proofs"
QR_PATH = Path(__file__).parent / "qr" / "qr.jpg"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ── User state (in-memory) ──────────────────────────────────────────────────
users = {}

# ── DB helpers ──────────────────────────────────────────────────────────────
def load_user_db():
    if DB_FILE.exists():
        try:
            return json.loads(DB_FILE.read_text("utf-8"))
        except Exception:
            return []
    return []

def save_user_db(ids):
    DB_FILE.write_text(json.dumps(ids), encoding="utf-8")

def register_user(chat_id: int):
    ids = load_user_db()
    if chat_id not in ids:
        ids.append(chat_id)
        save_user_db(ids)

# ── Keyboard ────────────────────────────────────────────────────────────────
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["🔓 Unban Account"], ["📂 See Proof / Past Cases", "👨‍💻 Contact Admin"]],
    resize_keyboard=True,
)

# ── /start ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    users[chat_id] = {"step": None}
    register_user(chat_id)

    welcome = (
        "🛡️ *INSTAGRAM ACCOUNT RECOVERY CENTER*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome\\! 👋 We specialize in reviewing disabled & banned Instagram accounts "
        "and guiding users through the official appeal process\\.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *WE HANDLE ALL BAN TYPES:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔴 *Integrity Violations*\n↳ Fake activity, spam behavior, bot use, misleading actions\n\n"
        "🔴 *Authenticity Issues*\n↳ Fake identity, impersonation, misleading profile\n\n"
        "🔴 *Community Guidelines*\n↳ Hate, harassment, nudity, violence, etc\\.\n\n"
        "🔴 *Spam Activity*\n↳ Mass follow/unfollow, repetitive comments, bulk DMs\n\n"
        "🔴 *Copyright / IP Violations*\n↳ Using others' content without permission\n\n"
        "🔴 *Fraud / Scam Activity*\n↳ Phishing, fake giveaways, money scams\n\n"
        "🔴 *Account Security Issues*\n↳ Suspicious login or hacked account behavior\n\n"
        "🔴 *Fake Engagement*\n↳ Buying followers, likes, or views\n\n"
        "🔴 *Restricted Goods / Services*\n↳ Promoting prohibited products\n\n"
        "🔴 *Repeated Violations*\n↳ Multiple rule breaks over time\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *YES — PERMANENT BANS CAN ALSO BE REVIEWED\\!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💼 Our team carefully reviews your case, identifies the exact violation reason, "
        "and prepares a strong appeal strategy tailored to your situation\\.\n\n"
        "⚠️ *Disclaimer:* We provide professional review & appeal guidance only\\. "
        "Final decision rests with Instagram\\. Unban is not guaranteed\\.\n\n"
        "👇 *Choose an option below to get started:*"
    )

    await update.message.reply_text(welcome, parse_mode="MarkdownV2", reply_markup=MAIN_KEYBOARD)

# ── /send <user_id> <message> (admin only) ───────────────────────────────────
async def send_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_chat.id
    if sender_id not in ADMIN_IDS:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: /send <user_id> <message>\n\nExample:\n/send 123456789 Your account is being reviewed."
        )
        return

    target_id = context.args[0]
    message = " ".join(context.args[1:])

    try:
        await context.bot.send_message(target_id, f"📩 *Message from Admin:*\n\n{message}", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Message sent to user {target_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send message to {target_id}.\nReason: {e}")

# ── /all <message> (admin only) ──────────────────────────────────────────────
async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_chat.id
    if sender_id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: /all <message>")
        return

    message = " ".join(context.args)
    all_users = load_user_db()

    await update.message.reply_text(f"📤 Sending to {len(all_users)} users...")

    sent, failed = 0, 0
    for uid in all_users:
        try:
            await context.bot.send_message(uid, f"📢 *Announcement:*\n\n{message}", parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"✅ Broadcast done!\n\n📨 Sent: {sent}\n❌ Failed: {failed}")

# ── Regular messages ─────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg = update.message

    # Ignore admins
    if chat_id in ADMIN_IDS:
        return

    if chat_id not in users:
        users[chat_id] = {"step": None}

    text = msg.text or ""

    try:
        # ── Unban Account ──
        if text == "🔓 Unban Account":
            users[chat_id]["step"] = "instagram_link"
            await msg.reply_text(
                "Okay ✅\n\nPlease send your Instagram profile link or username.\n\n"
                "Example:\nhttps://instagram.com/username\nor\n@username"
            )
            return

        # ── See Proof ──
        if text == "📂 See Proof / Past Cases":
            await msg.reply_text(
                "📂 *Real Proof — Accounts We've Recovered!*\n\nHere are some of our recent success cases 👇",
                parse_mode="Markdown"
            )

            images = sorted([
                f for f in PROOFS_DIR.iterdir()
                if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
            ])

            for image in images:
                await msg.reply_photo(photo=open(image, "rb"))

            await msg.reply_text(
                "✅ *These are just a few of our success cases!*\n\n"
                "📢 For 100+ more proofs, join our official channel:\n"
                "👉 https://t.me/rpunbanproofs",
                parse_mode="Markdown"
            )
            return

        # ── Contact Admin ──
        if text == "👨‍💻 Contact Admin":
            await msg.reply_text("Admin will contact you soon.\n\nYou can also message:\n@Rp_hu")
            return

        # ── Multi-step flow ──
        step = users[chat_id].get("step")

        if step == "instagram_link":
            users[chat_id]["instagram"] = text
            users[chat_id]["step"] = "email"
            await msg.reply_text("Now send your email linked with Instagram.")
            return

        if step == "email":
            users[chat_id]["email"] = text
            users[chat_id]["step"] = "phone"
            await msg.reply_text("Now send your phone number.")
            return

        if step == "phone":
            users[chat_id]["phone"] = text
            users[chat_id]["step"] = "awaiting_payment"

            username = f"@{msg.from_user.username}" if msg.from_user.username else "No username"
            info = (
                f"📥 New Instagram Appeal Request\n\n"
                f"User: {username}\n"
                f"Telegram ID: {chat_id}\n\n"
                f"Instagram: {users[chat_id]['instagram']}\n"
                f"Email: {users[chat_id]['email']}\n"
                f"Phone: {users[chat_id]['phone']}"
            )

            await context.bot.send_message(ADMIN_CHAT_ID, info)
            await context.bot.send_message(ADMIN_ID_2, info)

            await msg.reply_text(
                "✅ *Details Submitted Successfully!*\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💳 *PAYMENT REQUIRED — ₹50*\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "To proceed with your case review, please pay the one-time fee of *₹50*.\n\n"
                "📲 *Scan the QR code below to pay:*",
                parse_mode="Markdown"
            )

            await msg.reply_photo(
                photo=open(QR_PATH, "rb"),
                caption=(
                    "📸 *After payment, send the screenshot here.*\n\n"
                    "Our team will verify and start working on your case.\n\n"
                    "✅ *UNBAN IS 100% GUARANTEED!*\n"
                    "💰 *And if in any case it doesn't work — we will refund your money INSTANTLY. No questions asked.*"
                ),
                parse_mode="Markdown"
            )
            return

        # ── Payment screenshot ──
        if msg.photo:
            await context.bot.send_message(ADMIN_CHAT_ID, f"📸 Payment screenshot received from user {chat_id}")
            await context.bot.forward_message(ADMIN_CHAT_ID, chat_id, msg.message_id)
            await context.bot.send_message(ADMIN_ID_2, f"📸 Payment screenshot received from user {chat_id}")
            await context.bot.forward_message(ADMIN_ID_2, chat_id, msg.message_id)

            users[chat_id]["step"] = None

            await msg.reply_text(
                "💰 Payment Received ✅\n🚀 Work Started!",
                parse_mode="Markdown",
                reply_markup=MAIN_KEYBOARD
            )
            return

    except Exception as e:
        logging.error(f"Error for user {chat_id}: {e}")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_cmd))
    app.add_handler(CommandHandler("all", all_cmd))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()
