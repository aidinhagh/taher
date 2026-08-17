import telebot
import random
import os
import threading
import json
from flask import Flask
from telebot import types

# --- 1. Dummy Web Server to keep Render happy ---
app = Flask(__name__)

@app.route('/')
def keep_alive():
    return "Bot is alive and running!"

def run_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. Bot Setup & Cache System ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

CACHE_FILE = 'cached_ids.json'

def load_cached_ids():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cached_ids(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

# --- 3. The Automatic Setup Command ---
@bot.message_handler(commands=['setup'])
def setup_bot(message):
    bot.reply_to(message, "Uploading 14 videos to cache. This might take about 20 seconds...")
    cached_ids = load_cached_ids()
    
    # Loop from 1 to 14
    for i in range(1, 15):
        filename = f"{i}.mp4"
        try:
            with open(filename, 'rb') as video:
                # Upload the video silently
                msg = bot.send_animation(message.chat.id, video, disable_notification=True)
                # Automatically save the permanent ID
                cached_ids[str(i)] = msg.animation.file_id
                
                # Delete the message so it doesn't spam your chat
                bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.reply_to(message, f"Error with {filename}: {e}")
            return
            
    save_cached_ids(cached_ids)
    bot.reply_to(message, "✅ Setup complete! Inline mode and /roll are fully active for all 14 files.")

# --- 4. Standard /roll Command ---
@bot.message_handler(commands=['roll'])
def send_roll_gif(message):
    # Roll between 1 and 14
    roll_result = str(random.randint(1, 14))
    cached_ids = load_cached_ids()
    
    bot.reply_to(message, f"You rolled a {roll_result}!")
    
    if roll_result in cached_ids:
        # Use the cached Telegram ID if we have it
        bot.send_animation(message.chat.id, cached_ids[roll_result])
    else:
        # Fallback: Read from local file and cache it on the fly
        filename = f"{roll_result}.mp4"
        with open(filename, 'rb') as video:
            msg = bot.send_animation(message.chat.id, video)
            cached_ids[roll_result] = msg.animation.file_id
            save_cached_ids(cached_ids)

# --- 5. Inline Mode Handler ---
@bot.inline_handler(lambda query: True)
def handle_inline_query(inline_query):
    cached_ids = load_cached_ids()
    
    # Inline mode MUST have all 14 IDs ready.
    if len(cached_ids) < 14:
        result = types.InlineQueryResultArticle(
            id='error',
            title='Bot requires setup!',
            description='Please open my chat and send /setup to activate inline mode.',
            input_message_content=types.InputTextMessageContent('The bot owner needs to run /setup in my DM!')
        )
        bot.answer_inline_query(inline_query.id, [result], cache_time=0)
        return
        
    # Roll between 1 and 14
    roll_result = str(random.randint(1, 14))
    file_id = cached_ids.get(roll_result)
    
    # Send the cached file directly to the chat
    result = types.InlineQueryResultCachedMpeg4Gif(
        id='1',
        mpeg4_file_id=file_id,
        caption=f"I rolled a {roll_result}!"
    )
    bot.answer_inline_query(inline_query.id, [result], cache_time=0)

# --- 6. Start Everything ---
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    print("Bot is starting...")
    bot.infinity_polling()
