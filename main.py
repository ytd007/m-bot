import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from pymongo import MongoClient

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Environment Variables ලබා ගැනීම
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Connection
db_client = None
db = None

if MONGO_URI:
    try:
        db_client = MongoClient(MONGO_URI)
        db = db_client.get_database("telegram_bot_db")
        logging.info("Successfully connected to MongoDB Atlas!")
    except Exception as e:
        logging.error(f"MongoDB Connection Error: {e}")

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Save user to MongoDB
    if db is not None:
        try:
            users_collection = db["users"]
            users_collection.update_one(
                {"user_id": user.id},
                {"$set": {"first_name": user.first_name, "username": user.username}},
                upsert=True
            )
        except Exception as e:
            logging.error(f"Error saving user to DB: {e}")

    await update.message.reply_text(f"ආයුබෝවන් {user.first_name}! Bot එක සක්‍රියව ක්‍රියාත්මක වේ.")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if ADMIN_ID and user_id == str(ADMIN_ID):
        total_users = 0
        if db is not None:
            total_users = db["users"].count_documents({})
        await update.message.reply_text(f"👋 Admin Panel\n\nසම්පූර්ණ පරිශීලකයින් ගණන: {total_users}")
    else:
        await update.message.reply_text("ඔබට මෙම Command එක භාවිත කිරීමට අවසර නැත.")

if __name__ == '__main__':
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN සපයා නැත!")
        exit(1)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))

    logging.info("Bot is polling...")
    app.run_polling()
