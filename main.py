from datetime import datetime, timedelta
import logging
import os
from pymongo import MongoClient
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Configuration Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8916210991:AAHbUX2UePEW_JbE8AAsMQ9jjxnjb2QIIFc")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8507249474))
MONGO_URI = os.environ.get("MONGO_URI")

# MongoDB Database Connection Setup
client = MongoClient(MONGO_URI)
db = client["telegram_bot_db"]
users_col = db["users"]
messages_col = db["messages"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # User Database එකේ සිටීදැයි පරීක්ෂා කිරීම
    existing_user = users_col.find_one({"user_id": user_id})
    is_new_user = existing_user is None

    if is_new_user:
        users_col.insert_one({"user_id": user_id})

    await update.message.reply_text("සාදරයෙන් පිළිගන්නවා මනකාමිණී Bot වෙත,\n")

    # අලුත් User කෙනෙක් නම් පසුගිය පැය 24 Messages යැවීම
    if is_new_user:
        now = datetime.now()
        recent_messages = messages_col.find()

        for msg in recent_messages:
            msg_time = datetime.fromisoformat(msg["timestamp"])
            if now - msg_time <= timedelta(hours=24):
                try:
                    await context.bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=msg["chat_id"],
                        message_id=msg["message_id"],
                    )
                except Exception:
                    pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = update.effective_user.id

    if sender_id == ADMIN_ID:
        # Admin යවන Message එක Database එකේ Save කිරීම
        msg_data = {
            "chat_id": update.effective_chat.id,
            "message_id": update.message.message_id,
            "timestamp": datetime.now().isoformat(),
        }
        messages_col.insert_one(msg_data)

        # සියලුම Users ලාට Broadcast කිරීම
        all_users = users_col.find()
        success = 0
        failed = 0
        for u in all_users:
            try:
                await context.bot.copy_message(
                    chat_id=u["user_id"],
                    from_chat_id=update.effective_chat.id,
                    message_id=update.message.message_id,
                )
                success += 1
            except Exception:
                failed += 1

        await update.message.reply_text(
            f"Broadcast සාර්ථකයි!\nයැවූ ගණන: {success}\nඅසාර්ථක වූ ගණන: {failed}"
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    print("Bot එක සාර්ථකව Run වෙමින් පවතී...")
    app.run_polling()