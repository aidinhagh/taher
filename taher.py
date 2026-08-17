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
    bot.reply_to(message, "Uploading 15 videos (Cover + 14 Rolls) to cache. This takes about 20 seconds...")
    cached_ids = load_cached_ids()
    
    # Loop from 0 to 14 (0 is our mystery cover!)
    for i in range(0, 15):
        filename = f"{i}.mp4"
        try:
            with open(filename, 'rb') as video:
                msg = bot.send_animation(message.chat.id, video, disable_notification=True)
                cached_ids[str(i)] = msg.animation.file_id
                bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.reply_to(message, f"Error with {filename}: {e}")
            return
            
    save_cached_ids(cached_ids)
    bot.reply_to(message, "✅ Setup complete! The mystery inline mode is ready.")

# --- 4. Standard /roll Command ---
@bot.message_handler(commands=['roll'])
def send_roll_gif(message):
    roll_result = str(random.randint(1, 14))
    cached_ids = load_cached_ids()
    
    if roll_result in cached_ids:
        bot.send_animation(message.chat.id, cached_ids[roll_result])
    else:
        filename = f"{roll_result}.mp4"
        with open(filename, 'rb') as video:
            msg = bot.send_animation(message.chat.id, video)
            cached_ids[roll_result] = msg.animation.file_id
            save_cached_ids(cached_ids)

# --- 5. Inline Mode: The Mystery Box! ---
@bot.inline_handler(lambda query: True)
def handle_inline_query(inline_query):
    cached_ids = load_cached_ids()
    
    if len(cached_ids) < 15:
        result = types.InlineQueryResultArticle(
            id='error',
            title='Bot requires setup!',
            description='Please open my chat and send /setup.',
            input_message_content=types.InputTextMessageContent('The bot owner needs to run /setup!')
        )
        bot.answer_inline_query(inline_query.id, [result], cache_time=0)
        return
        
    # Get the ID of the mystery cover video (0.mp4)
    cover_id = cached_ids.get("0")
    
    # Create the "Reveal" button attached to the video
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎲 Click to Reveal Roll!", callback_data="reveal_roll"))
    
    # Send ONLY the mystery cover to the inline menu
    result = types.InlineQueryResultCachedMpeg4Gif(
        id='mystery_roll',
        mpeg4_file_id=cover_id,
        caption="🎲 Rolling the dice...",
        reply_markup=markup
    )
    bot.answer_inline_query(inline_query.id, [result], cache_time=0)

# --- 6. Handle the Button Click! ---
@bot.callback_query_handler(func=lambda call: call.data == 'reveal_roll')
def handle_reveal(call):
    cached_ids = load_cached_ids()
    
    # Roll the random number NOW, so it's a true surprise!
    roll_result = str(random.randint(1, 14))
    file_id = cached_ids.get(roll_result)
    
    # Swap the cover video for the real roll!
    media = types.InputMediaAnimation(media=file_id, caption=f"I rolled a {roll_result}!")
    
    try:
        # Edit the message in the chat
        bot.edit_message_media(media=media, inline_message_id=call.inline_message_id)
        # Tell Telegram to stop spinning the loading circle on the button
        bot.answer_callback_query(call.id, "Revealed!")
    except Exception as e:
        print(f"Error revealing: {e}")

# --- 7. Start Everything ---
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    print("Bot is starting...")
    bot.infinity_polling()
