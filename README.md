# 🤖 Mr. LeetCode Bot

A Telegram bot designed to help you build and maintain consistent LeetCode solving habits through streak tracking, daily reminders, and group leaderboards.

## ✨ Features

### 🎯 Core Functionality

- **Problem Logging**: Log your daily LeetCode submissions with difficulty and comments
- **Streak Tracking**: Automatic streak calculation with daily reset system
- **Multi-Group Support**: Works across multiple Telegram groups with group-specific leaderboards
- **Interactive UI**: Easy-to-use buttons for difficulty selection

### 📅 Automated Scheduling

- **Daily Reminders**: Morning motivation messages at 8:00 AM SGT
- **Leaderboards**: Automatic leaderboard posting at midnight SGT
- **Streak Reset**: Automatic streak reset at midnight for inactive users
- **Message Pinning**: Pins leaderboard messages for visibility (requires admin permissions)

### 🏆 Leaderboard System

- **Group-Specific Rankings**: Each group has its own leaderboard
- **Current & Best Streaks**: Track both ongoing and personal record streaks
- **Medal System**: Gold, silver, bronze medals for top performers
- **Real-time Updates**: Instant streak updates after each submission

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Supabase account and project

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/mr_leet_bot.git
   cd mr_leet_bot
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the project root:

   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   ```

4. **Set up the database**

   Execute these SQL commands in your Supabase SQL editor:

   ```sql
   -- Users table
   CREATE TABLE users (
       id SERIAL PRIMARY KEY,
       user_id BIGINT UNIQUE NOT NULL,
       username TEXT NOT NULL,
       current_streak INTEGER DEFAULT 0,
       best_streak INTEGER DEFAULT 0,
       last_checkin DATE,
       created_at TIMESTAMP DEFAULT NOW()
   );

   -- Groups table
   CREATE TABLE groups (
       id SERIAL PRIMARY KEY,
       chat_id BIGINT UNIQUE NOT NULL,
       chat_title TEXT,
       added_date DATE DEFAULT CURRENT_DATE,
       created_at TIMESTAMP DEFAULT NOW()
   );

   -- Group members table
   CREATE TABLE group_members (
       id SERIAL PRIMARY KEY,
       user_id BIGINT NOT NULL,
       chat_id BIGINT NOT NULL,
       joined_at TIMESTAMP DEFAULT NOW(),
       UNIQUE(user_id, chat_id)
   );

   -- Submissions table
   CREATE TABLE submissions (
       id SERIAL PRIMARY KEY,
       user_id BIGINT NOT NULL,
       chat_id BIGINT NOT NULL,
       date DATE NOT NULL,
       problem_title TEXT NOT NULL,
       difficulty TEXT NOT NULL,
       comment TEXT,
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

5. **Run the bot**
   ```bash
   python bot.py
   ```

## 📖 Usage

### Bot Commands

- `/start` - Register with the bot and join the current group
- `/done` - Log a new LeetCode problem submission
- `/set_group_chat_id` - Set up the current group for automated features
- `/cancel` - Cancel the current submission process

### Logging a Problem

1. Use `/done` command
2. Enter the problem title (copy from LeetCode)
3. Select difficulty (Easy/Medium/Hard) using buttons
4. Add your thoughts/comments about the problem
5. ✅ Submission logged and streak updated!

### Group Setup

1. Add the bot to your Telegram group
2. Make the bot an admin (optional, for message pinning)
3. Use `/set_group_chat_id` to activate automated features
4. Start coding! 🚀

## 🛠️ Deployment

### Railway (Recommended)

1. Push your code to GitHub
2. Create a `Procfile` in your project root:
   ```
   worker: python bot.py
   ```
3. Go to [Railway.app](https://railway.app) and connect your repository
4. Add environment variables in Railway dashboard
5. Deploy!

### Other Options

- **Heroku**: Similar process with Heroku CLI
- **Render**: Deploy as a background worker
- **DigitalOcean App Platform**: Deploy as a worker service
- **VPS**: For full control with systemd service

## 🏗️ Project Structure

```
mr_leet_bot/
├── bot.py              # Main bot application
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create this)
├── Procfile           # For deployment
└── README.md          # This file
```

## 🔧 Configuration

### Timezone Settings

The bot is configured for Singapore timezone (SGT). To change:

```python
SGT = timezone("Your/Timezone")  # e.g., "US/Eastern", "Europe/London"
```

### Scheduling Times

Modify the scheduler in `bot.py`:

```python
scheduler.add_job(send_reminders_job, "cron", hour=8, minute=0)     # Reminders
scheduler.add_job(post_leaderboard_job, "cron", hour=0, minute=0)   # Leaderboard
scheduler.add_job(reset_daily_streaks_job, "cron", hour=0, minute=0) # Reset
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

**Bot not responding**

- Check if environment variables are set correctly
- Verify Telegram bot token is valid
- Ensure Supabase credentials are correct

**Database errors**

- Verify all tables are created in Supabase
- Check if Supabase URL and key are correct
- Ensure tables have proper permissions

**Timezone issues**

- Install `pytz` package: `pip install pytz`
- Verify timezone string is correct

**Scheduling not working**

- Check server timezone vs. bot timezone
- Verify deployment platform supports background jobs

## 📞 Support

- Create an issue on GitHub
- Contact [@iamrolling](https://t.me/iamrolling) on Telegram

## 🎉 Acknowledgments

- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Database powered by [Supabase](https://supabase.com)
- Scheduling by [APScheduler](https://apscheduler.readthedocs.io/)

---

Made with ❤️ for the coding community. Keep grinding those LeetCode problems! 💪
