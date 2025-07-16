import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, ChatMemberHandler
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define conversation states
PROBLEM_NAME, DIFFICULTY, COMMENT = range(3)

# Define timezone for Singapore
SGT = timezone("Asia/Singapore")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register a user in the database."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Check if user already exists
    response = supabase.table("users").select("*").eq("user_id", user.id).execute()

    if response.data:
        # Add user to this group if not already a member
        existing_membership = supabase.table("group_members").select("*").eq("user_id", user.id).eq("chat_id", chat_id).execute()
        if not existing_membership.data:
            supabase.table("group_members").insert({
                "user_id": user.id,
                "chat_id": chat_id
            }).execute()
        
        await update.message.reply_text("You are already registered!")
    else:
        # Register the user
        supabase.table("users").insert({
            "user_id": user.id,
            "username": user.username or user.full_name,
            "current_streak": 0,
            "best_streak": 0,
            "last_checkin": None
        }).execute()

        # Add user to this group
        supabase.table("group_members").insert({
            "user_id": user.id,
            "chat_id": chat_id
        }).execute()

        # Send welcome message with menu
        menu = ReplyKeyboardMarkup([
            ["/done", "/help"]
        ], resize_keyboard=True)

        await update.message.reply_text(
            "Welcome to the LeetCode Habit Bot! Use /done to log your progress.",
            reply_markup=menu
        )

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the check-in process."""
    await update.message.reply_text("What is the title of the problem you solved? (Copy from leetcode)")
    return PROBLEM_NAME

async def problem_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture the problem name."""
    context.user_data["problem_name"] = update.message.text

    # Define difficulty buttons
    difficulty_buttons = [
        [InlineKeyboardButton("Easy", callback_data="easy"),
         InlineKeyboardButton("Medium", callback_data="medium"),
         InlineKeyboardButton("Hard", callback_data="hard")]
    ]
    reply_markup = InlineKeyboardMarkup(difficulty_buttons)

    await update.message.reply_text("What is the difficulty?", reply_markup=reply_markup)
    return DIFFICULTY

async def difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture the difficulty from button press."""
    query = update.callback_query
    await query.answer()

    difficulty = query.data
    context.user_data["difficulty"] = difficulty

    await query.edit_message_text("What were your thoughts on the problem?")
    return COMMENT

async def comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture the optional comment and log the submission."""
    context.user_data["comment"] = update.message.text

    user = update.effective_user
    chat_id = update.effective_chat.id
    problem_name = context.user_data["problem_name"]
    difficulty = context.user_data["difficulty"]
    comment = context.user_data["comment"]

    # Log the submission in the database with chat_id
    supabase.table("submissions").insert({
        "user_id": user.id,
        "chat_id": chat_id,
        "date": str(update.message.date.date()),
        "problem_title": problem_name,
        "difficulty": difficulty,
        "comment": comment
    }).execute()

    # Update streak in the database
    user_data = supabase.table("users").select("current_streak", "best_streak", "last_checkin").eq("user_id", user.id).execute().data[0]

    # Update streak logic based on consecutive days
    last_checkin = user_data["last_checkin"]
    current_date = update.message.date.date()

    if last_checkin:
        last_checkin_date = datetime.strptime(last_checkin, "%Y-%m-%d").date()
        if (current_date - last_checkin_date).days == 1:
            current_streak = user_data["current_streak"] + 1
        else:
            current_streak = 1
    else:
        current_streak = 1

    best_streak = max(user_data["best_streak"], current_streak)

    supabase.table("users").update({
        "current_streak": current_streak,
        "best_streak": best_streak,
        "last_checkin": str(current_date)
    }).eq("user_id", user.id).execute()

    await update.message.reply_text(
        f"🎉 Submission logged! 🎉\n"
        f"Problem Title: <b>{problem_name}</b>\n"
        f"Difficulty: <b>{difficulty.capitalize()}</b>\n"
        f"Comment: <b>{comment if comment else 'No comments provided.'}</b>\n"
        f"Your current streak is <b>{current_streak}</b> days. Keep it up!",
        parse_mode="HTML"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    await update.message.reply_text("Check-in canceled.")
    return ConversationHandler.END

async def set_group_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the group chat ID when the bot is added to a group."""
    chat_id = update.effective_chat.id
    
    # Store the group chat ID in the database
    try:
        # Check if group already exists
        existing_group = supabase.table("groups").select("*").eq("chat_id", chat_id).execute()
        
        if not existing_group.data:
            # Insert new group
            supabase.table("groups").insert({
                "chat_id": chat_id,
                "chat_title": update.effective_chat.title or "Unknown Group",
                "added_date": str(datetime.now().date())
            }).execute()
        
        await update.message.reply_text(
            f"✅ Group chat ID set successfully!\n\n"
            f"🎯 Chat ID: {chat_id}\n\n"
            f"📅 Scheduled Features Now Active:\n"
            f"• 🌅 Good morning reminders at 8:00 AM SGT\n"
            f"• 🏆 Daily leaderboard at 8:00 AM & 8:00 PM SGT\n\n"
            f"🚀 Ready to track your coding journey!"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error setting up group: {e}")
        print(f"Error in set_group_chat_id: {e}")

async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when the bot is added to a group."""
    if update.my_chat_member.new_chat_member.status == "member":
        await update.effective_chat.send_message(
            "Hello everyone! 🎉\n"
            "I'm the LeetCode Habit Bot, here to help you track your coding progress and stay consistent!\n\n"
            "🚀 Here's what I can do for you:\n"
            "• Use /done to log your daily problem submissions\n"
            "• Use /set_group_chat_id to set this group for reminders and leaderboard updates\n"
            "• Check out the leaderboard to see who has the longest streaks!\n\n"
            "💻 Let's code and grow together!\n"
            "Created by @iamrolling 👨‍�"
        )

# Function to send reminders
async def send_reminders():
    # Get all active groups from database
    try:
        groups = supabase.table("groups").select("chat_id").execute().data
        for group in groups:
            await application.bot.send_message(
                chat_id=group["chat_id"], 
                text="🌅 Good morning, coding warriors! ☀️\n\n"
                     "📚 Time for your daily LeetCode challenge!\n"
                     "💪 Keep that streak alive and use /done to log your progress.\n\n"
                     "🎯 Remember: Consistency is the key to mastery! 🚀"
            )
    except Exception as e:
        print(f"❌ Error in send_reminders: {e}")

# Function to post leaderboard
async def post_leaderboard():
    # Send to all active groups
    try:
        groups = supabase.table("groups").select("chat_id, chat_title").execute().data
        for group in groups:
            chat_id = group["chat_id"]
            
            # Get users specific to this group with their stats
            group_users = supabase.table("group_members").select("user_id").eq("chat_id", chat_id).execute().data
            user_ids = [member["user_id"] for member in group_users]
            
            if not user_ids:
                continue  # Skip groups with no members
            
            # Get user stats for this group only
            users = supabase.table("users").select("username, current_streak, best_streak").in_("user_id", user_ids).order("current_streak", desc=True).execute().data
            
            if not users:
                continue  # Skip if no users found
            
            # Build group-specific leaderboard
            leaderboard = f"🌟🏆 LeetCode Leaderboard 🏆🌟\n"
            leaderboard += f"📍 Group: {group.get('chat_title', 'Unknown Group')}\n\n"
            
            for idx, user in enumerate(users, start=1):
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "✨"
                leaderboard += f"{medal} {idx}. {user['username']} - Current Streak: {user['current_streak']} days, Best Streak: {user['best_streak']} days\n"
            
            # Send the leaderboard message
            message = await application.bot.send_message(chat_id=chat_id, text=leaderboard)
            
            # Try to pin the message
            try:
                await application.bot.pin_chat_message(chat_id=chat_id, message_id=message.message_id)
                print(f"✅ Leaderboard message pinned successfully in group {chat_id}!")
            except Exception as e:
                print(f"❌ Failed to pin message in group {chat_id}: {e}")
                # Send a reminder message if pinning fails
                await application.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Unable to pin the leaderboard message.\n"
                         "Please make me an admin to enable message pinning! 📌"
                )
    except Exception as e:
        print(f"❌ Error in post_leaderboard: {e}")

# Function to reset streaks at midnight for users who didn't submit today
async def reset_daily_streaks():
    """Reset current streaks for users who didn't submit today."""
    try:
        print("🌙 Starting daily streak reset check...")
        
        # Get current date in Singapore timezone
        current_date = datetime.now(SGT).date()
        yesterday = current_date - timedelta(days=1)
        
        # Get all users
        all_users = supabase.table("users").select("user_id, username, current_streak, last_checkin").execute().data
        
        reset_count = 0
        for user in all_users:
            user_id = user["user_id"]
            last_checkin = user["last_checkin"]
            current_streak = user["current_streak"]
            
            # Skip if user already has 0 streak
            if current_streak == 0:
                continue
                
            # Check if user submitted yesterday
            if last_checkin:
                last_checkin_date = datetime.strptime(last_checkin, "%Y-%m-%d").date()
                
                # If last check-in was not yesterday, reset streak
                if last_checkin_date != yesterday:
                    supabase.table("users").update({
                        "current_streak": 0
                    }).eq("user_id", user_id).execute()
                    
                    print(f"🔄 Reset streak for user {user['username']} (was {current_streak} days)")
                    reset_count += 1
            else:
                # No previous check-in, reset streak
                supabase.table("users").update({
                    "current_streak": 0
                }).eq("user_id", user_id).execute()
                
                print(f"🔄 Reset streak for user {user['username']} (was {current_streak} days)")
                reset_count += 1
        
        print(f"✅ Daily streak reset completed! Reset {reset_count} users' streaks.")
        
        # Send notification to all groups about the reset
        groups = supabase.table("groups").select("chat_id").execute().data
        for group in groups:
            await application.bot.send_message(
                chat_id=group["chat_id"],
                text="🌙 Daily reset complete! 🌙\n\n"
                     "⏰ It's a new day in Singapore!\n"
                     f"🔄 {reset_count} streaks were reset for inactive users.\n\n"
                     "🚀 Ready for today's LeetCode challenge? Use /done to start your streak!"
            )
            
    except Exception as e:
        print(f"❌ Error in reset_daily_streaks: {e}")

# Wrapper function for daily reset job
def reset_daily_streaks_job():
    print("🌙 reset_daily_streaks_job called!")
    
    import asyncio
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("Created new event loop for scheduler thread")
        
        # Run the coroutine
        loop.run_until_complete(reset_daily_streaks())
        print("✅ reset_daily_streaks_job completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in reset_daily_streaks_job: {e}")
    finally:
        try:
            loop.close()
        except:
            pass

# Wrapper functions for scheduler jobs
def send_reminders_job():
    print("📅 send_reminders_job called!")
    
    import asyncio
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("Created new event loop for scheduler thread")
        
        # Run the coroutine
        loop.run_until_complete(send_reminders())
        print("✅ send_reminders_job completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in send_reminders_job: {e}")
    finally:
        try:
            loop.close()
        except:
            pass

def post_leaderboard_job():
    print("📊 post_leaderboard_job called!")
    
    import asyncio
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        print("Created new event loop for scheduler thread")
        
        # Run the coroutine
        loop.run_until_complete(post_leaderboard())
        print("✅ post_leaderboard_job completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in post_leaderboard_job: {e}")
    finally:
        try:
            loop.close()
        except:
            pass

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_group_chat_id", set_group_chat_id))

    # Add conversation handler for /done
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("done", done)],
        states={
            PROBLEM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, problem_name)],
            DIFFICULTY: [CallbackQueryHandler(difficulty)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    application.add_handler(conv_handler)

    # Add handler for welcome message
    application.add_handler(ChatMemberHandler(welcome_message, ChatMemberHandler.MY_CHAT_MEMBER))

    # Initialize scheduler
    scheduler = BackgroundScheduler(timezone=SGT)
    
    # Schedule reminders and leaderboards
    scheduler.add_job(send_reminders_job, "cron", hour=8, minute=0)  # 8 AM SGT
    scheduler.add_job(post_leaderboard_job, "cron", hour=0, minute=0)  # Midnight SGT
    scheduler.add_job(reset_daily_streaks_job, "cron", hour=0, minute=0)  # Midnight SGT
    
    scheduler.start()

    # Start the bot
    application.run_polling()