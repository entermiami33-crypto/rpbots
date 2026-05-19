require("dotenv").config();
const TelegramBot = require("node-telegram-bot-api");
const path = require("path");
const fs = require("fs");

const bot = new TelegramBot(process.env.BOT_TOKEN, { polling: true });

const ADMIN_CHAT_ID = process.env.ADMIN_CHAT_ID;

// Parse admin IDs
const ADMIN_ID = parseInt(ADMIN_CHAT_ID);
const ADMIN_ID_2 = 6514315888;
const ADMIN_IDS = [ADMIN_ID, ADMIN_ID_2];
const users = {};

const mainKeyboard = {
  reply_markup: {
    keyboard: [
      ["🔓 Unban Account"],
      ["📂 See Proof / Past Cases", "👨‍💻 Contact Admin"]
    ],
    resize_keyboard: true
  }
};

bot.onText(/\/send (.+)/, async (msg, match) => {
  const senderId = msg.chat.id;

  // Only admins can use this
  if (!ADMIN_IDS.includes(senderId)) return;

  const parts = match[1].split(" ");
  const targetId = parts[0];
  const message = parts.slice(1).join(" ");

  if (!targetId || !message) {
    return bot.sendMessage(senderId, `❌ Usage: /send <user_id> <message>\n\nExample:\n/send 123456789 Your account is being reviewed.`);
  }

  try {
    await bot.sendMessage(targetId, `📩 *Message from Admin:*\n\n${message}`, { parse_mode: "Markdown" });
    bot.sendMessage(senderId, `✅ Message sent to user ${targetId}`);
  } catch (err) {
    bot.sendMessage(senderId, `❌ Failed to send message to ${targetId}.\nReason: ${err.message}`);
  }
});

bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;

  users[chatId] = { step: null };

  const welcomeMessage = `🛡️ *INSTAGRAM ACCOUNT RECOVERY CENTER*
━━━━━━━━━━━━━━━━━━━━━━

Welcome! 👋 We specialize in reviewing disabled & banned Instagram accounts and guiding users through the official appeal process.

━━━━━━━━━━━━━━━━━━━━━━
📋 *WE HANDLE ALL BAN TYPES:*
━━━━━━━━━━━━━━━━━━━━━━

🔴 *Integrity Violations*
↳ Fake activity, spam behavior, bot use, misleading actions

🔴 *Authenticity Issues*
↳ Fake identity, impersonation, misleading profile

🔴 *Community Guidelines*
↳ Hate, harassment, nudity, violence, etc.

🔴 *Spam Activity*
↳ Mass follow/unfollow, repetitive comments, bulk DMs

🔴 *Copyright / IP Violations*
↳ Using others' content without permission

🔴 *Fraud / Scam Activity*
↳ Phishing, fake giveaways, money scams

🔴 *Account Security Issues*
↳ Suspicious login or hacked account behavior

🔴 *Fake Engagement*
↳ Buying followers, likes, or views

🔴 *Restricted Goods / Services*
↳ Promoting prohibited products

🔴 *Repeated Violations*
↳ Multiple rule breaks over time

━━━━━━━━━━━━━━━━━━━━━━
✅ *YES — PERMANENT BANS CAN ALSO BE REVIEWED!*
━━━━━━━━━━━━━━━━━━━━━━

💼 Our team carefully reviews your case, identifies the exact violation reason, and prepares a strong appeal strategy tailored to your situation.

⚠️ *Disclaimer:* We provide professional review & appeal guidance only. Final decision rests with Instagram. Unban is not guaranteed.

👇 *Choose an option below to get started:*`;

  bot.sendMessage(chatId, welcomeMessage, {
    parse_mode: "Markdown",
    ...mainKeyboard
  }).catch(err => {
    if (err.response && err.response.statusCode === 403) {
      console.log(`User ${chatId} has blocked the bot. Skipping.`);
    }
  });
});

bot.on("message", async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  // Ignore messages from admin
  if (ADMIN_IDS.includes(chatId)) return;

  if (!users[chatId]) users[chatId] = { step: null };

  if (text === "/start") return;

  try {

  if (text === "🔓 Unban Account") {
    users[chatId].step = "instagram_link";

    return bot.sendMessage(
      chatId,
      `Okay ✅

Please send your Instagram profile link or username.

Example:
https://instagram.com/username
or
@username`
    );
  }

  if (text === "📂 See Proof / Past Cases") {
    await bot.sendMessage(
      chatId,
      `📂 *Real Proof — Accounts We've Recovered!*\n\nHere are some of our recent success cases 👇`,
      { parse_mode: "Markdown" }
    );

    const proofsDir = path.join(__dirname, "proofs");
    const files = fs.readdirSync(proofsDir);

    const images = files.filter(f => ["jpg", "jpeg", "png", "webp"].includes(f.split(".").pop().toLowerCase()));

    // Send images only
    for (const file of images) {
      await bot.sendPhoto(chatId, path.join(proofsDir, file));
    }

    // Then channel link message
    await bot.sendMessage(
      chatId,
      `✅ *These are just a few of our success cases!*\n\n📢 For 100+ more proofs, join our official channel:\n👉 https://t.me/rpunbanproofs`,
      { parse_mode: "Markdown" }
    );

    return;
  }

  if (text === "👨‍💻 Contact Admin") {
    return bot.sendMessage(
      chatId,
      `Admin will contact you soon.\n\nYou can also message:\n@Rp_hu`
    );
  }

  if (users[chatId].step === "instagram_link") {
    users[chatId].instagram = text;
    users[chatId].step = "email";

    return bot.sendMessage(chatId, "Now send your email linked with Instagram.");
  }

  if (users[chatId].step === "email") {
    users[chatId].email = text;
    users[chatId].step = "phone";

    return bot.sendMessage(chatId, "Now send your phone number.");
  }

  if (users[chatId].step === "phone") {
    users[chatId].phone = text;
    users[chatId].step = "awaiting_payment";

    const username = msg.from.username ? `@${msg.from.username}` : "No username";

    await bot.sendMessage(
      ADMIN_CHAT_ID,
      `📥 New Instagram Appeal Request

User: ${username}
Telegram ID: ${chatId}

Instagram: ${users[chatId].instagram}
Email: ${users[chatId].email}
Phone: ${users[chatId].phone}`
    );

    await bot.sendMessage(
      ADMIN_ID_2,
      `📥 New Instagram Appeal Request

User: ${username}
Telegram ID: ${chatId}

Instagram: ${users[chatId].instagram}
Email: ${users[chatId].email}
Phone: ${users[chatId].phone}`
    );

    await bot.sendMessage(
      chatId,
      `✅ *Details Submitted Successfully!*

━━━━━━━━━━━━━━━━━━━━━━
💳 *PAYMENT REQUIRED — ₹50*
━━━━━━━━━━━━━━━━━━━━━━

To proceed with your case review, please pay the one-time fee of *₹50*.

📲 *Scan the QR code below to pay:*`,
      { parse_mode: "Markdown" }
    );

    const qrPath = path.join(__dirname, "qr", "qr.jpg");

    await bot.sendPhoto(chatId, qrPath, {
      caption: `📸 *After payment, send the screenshot here.*\n\nOur team will verify and start working on your case.\n\n✅ *UNBAN IS 100% GUARANTEED!*\n💰 *And if in any case it doesn't work — we will refund your money INSTANTLY. No questions asked.*`,
      parse_mode: "Markdown"
    });

    return;
  }

  if (msg.photo) {
    await bot.sendMessage(ADMIN_CHAT_ID, `📸 Payment screenshot received from user ${chatId}`);
    await bot.forwardMessage(ADMIN_CHAT_ID, chatId, msg.message_id);

    await bot.sendMessage(ADMIN_ID_2, `📸 Payment screenshot received from user ${chatId}`);
    await bot.forwardMessage(ADMIN_ID_2, chatId, msg.message_id);

    users[chatId].step = null;

    return bot.sendMessage(
      chatId,
      `💰 Payment Received ✅\n🚀 Work Started!`,
      { parse_mode: "Markdown", ...mainKeyboard }
    );
  }

  } catch (err) {
    if (err.response && err.response.statusCode === 403) {
      console.log(`User ${chatId} has blocked the bot. Skipping.`);
    } else {
      console.error(`Error for user ${chatId}:`, err.message);
    }
  }
});

console.log("Bot running...");