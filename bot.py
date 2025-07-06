import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from supabase import create_client, Client
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Scheduler for daily reminders
scheduler = BackgroundScheduler()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register a user in the database."""
    user = update.effective_user
    response = supabase.table("users").upsert({
        "telegram_id": user.id,
        "name": user.full_name
    }, on_conflict=["telegram_id"]).execute()

    print("/start command invoked")
    print(f"User ID: {user.id}, Name: {user.full_name}")
    print("Supabase response:", response)

    if response.data:
        print("User successfully registered or updated.")
        # Define the menu options
        menu = ReplyKeyboardMarkup([
            ["/start", "/submit", "/help"]
        ], resize_keyboard=True)

        # Send the menu to the user
        await update.message.reply_text(
            f"Welcome, {user.full_name}! You're now registered.",
            reply_markup=menu
        )
    else:
        print("Error occurred during registration.")
        await update.message.reply_text("An error occurred while registering. Please try again.")

async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log a problem submission."""
    user = update.effective_user
    args = context.args

    if len(args) < 3:
        await update.message.reply_text("Usage: /submit <problem_name> <difficulty> <thoughts>")
        return

    problem_name = args[0]
    difficulty = args[1]
    thoughts = " ".join(args[2:])

    # Insert submission into the database
    response = supabase.table("submissions").insert({
        "user_id": user.id,
        "problem_name": problem_name,
        "difficulty": difficulty,
        "thoughts": thoughts
    }).execute()

    if response.status_code == 201:
        await update.message.reply_text("Submission logged successfully!")
    else:
        await update.message.reply_text("Failed to log submission. Please try again.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a list of available commands."""
    help_text = (
        "Available commands:\n"
        "/start - Register yourself with the bot\n"
        "/submit <problem_name> <difficulty> <thoughts> - Log a problem submission\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

def send_daily_reminder():
    """Send a daily reminder to the group."""
    # Replace with your group chat ID
    group_chat_id = "-1001234567890"
    application.bot.send_message(chat_id=group_chat_id, text="Don't forget to solve a LeetCode problem today!")

if __name__ == "__main__":
    # Initialize the bot
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Set bot commands for dropdown menu
    application.bot.set_my_commands([
        ("start", "Register yourself with the bot"),
        ("submit", "Log a problem submission"),
        ("help", "Show help message")
    ])

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("submit", submit))
    application.add_handler(CommandHandler("help", help_command))

    # Schedule daily reminders
    scheduler.add_job(send_daily_reminder, "cron", hour=9)  # Sends at 9 AM daily
    scheduler.start()

    # Start the bot
    application.run_polling()
