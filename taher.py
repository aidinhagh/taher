import telebot
import random
import os
import threading
import json
import time
from flask import Flask
from telebot import types

# --- 1. Dummy Web Server ---
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
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cached_ids(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

# --- 3. The Automatic Setup Command ---
@bot.message_handler(commands=['setup'])
def setup_bot(message):
    bot.reply_to(message, "Uploading files to cache... please wait.")
    cached_ids = load_cached_ids()
    
    for i in range(0, 15):
        filename = f"{i}.mp4"
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as video:
                    msg = bot.send_animation(message.chat.id, video, disable_notification=True)
                    cached_ids[str(i)] = msg.animation.file_id
                    bot.delete_message(message.chat.id, msg.message_id)
            except Exception:
                pass
    
    for i in range(1, 7):
        filename = f"dice{i}.mp4"
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as video:
                    msg = bot.send_animation(message.chat.id, video, disable_notification=True)
                    cached_ids[f"dice_{i}"] = msg.animation.file_id
                    bot.delete_message(message.chat.id, msg.message_id)
            except Exception:
                pass
                
    save_cached_ids(cached_ids)
    bot.reply_to(message, "✅ Setup complete!")

# --- 4. Standard /roll Command ---
@bot.message_handler(commands=['roll'])
def send_roll_gif(message):
    roll_result = str(random.randint(1, 14))
    cached_ids = load_cached_ids()
    bot.reply_to(message, f"You rolled a {roll_result}!")
    
    if roll_result in cached_ids:
        bot.send_animation(message.chat.id, cached_ids[roll_result])
    else:
        filename = f"{roll_result}.mp4"
        if os.path.exists(filename):
            with open(filename, 'rb') as video:
                msg = bot.send_animation(message.chat.id, video)
                cached_ids[roll_result] = msg.animation.file_id
                save_cached_ids(cached_ids)

# --- 5. Keyword Scanner for "taher" / "طاهر" ---
@bot.message_handler(func=lambda message: message.text and ('taher' in message.text.lower() or 'طاهر' in message.text))
def handle_taher_trigger(message):
    roll_result = str(random.randint(1, 14))
    cached_ids = load_cached_ids()
    
    if roll_result in cached_ids:
        bot.send_animation(message.chat.id, cached_ids[roll_result], reply_to_message_id=message.message_id)
    else:
        filename = f"{roll_result}.mp4"
        if os.path.exists(filename):
            with open(filename, 'rb') as video:
                msg = bot.send_animation(message.chat.id, video, reply_to_message_id=message.message_id)
                cached_ids[roll_result] = msg.animation.file_id
                save_cached_ids(cached_ids)

# --- 6. The Manual Dice Reactor ---
# If anyone sends a dice emoji in the chat, the bot will instantly react to it!
@bot.message_handler(content_types=['dice'])
def handle_dice(message):
    if message.dice.emoji == '🎲':
        roll_value = message.dice.value 
        time.sleep(4) # Wait 4 seconds for the animation to land
        
        cached_ids = load_cached_ids()
        cache_key = f"dice_{roll_value}"
        
        if cache_key in cached_ids:
            bot.send_animation(message.chat.id, cached_ids[cache_key], reply_to_message_id=message.message_id)
        else:
            filename = f"dice{roll_value}.mp4"
            if os.path.exists(filename):
                with open(filename, 'rb') as video:
                    msg = bot.send_animation(message.chat.id, video, reply_to_message_id=message.message_id)
                    cached_ids[cache_key] = msg.animation.file_id
                    save_cached_ids(cached_ids)

# --- 7. Inline Mode: The Mystery Box! ---
@bot.inline_handler(lambda query: True)
def handle_inline_query(inline_query):
    cached_ids = load_cached_ids()
    cover_id = cached_ids.get("0")
    
    if not cover_id:
        result = types.InlineQueryResultArticle(
            id='error',
            title='Bot requires setup!',
            description='Please open my chat and send /setup.',
            input_message_content=types.InputTextMessageContent('The bot owner needs to run /setup in my DM!')
        )
        bot.answer_inline_query(inline_query.id, [result], cache_time=0)
        return
        
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎲 Click to Reveal Taher!", callback_data="reveal_roll"))
    
    result = types.InlineQueryResultCachedMpeg4Gif(
        id='mystery_roll',
        mpeg4_file_id=cover_id,
        caption="Summoning Taher...",
        reply_markup=markup
    )
    bot.answer_inline_query(inline_query.id, [result], cache_time=0)

@bot.callback_query_handler(func=lambda call: call.data == 'reveal_roll')
def handle_reveal(call):
    cached_ids = load_cached_ids()
    roll_result = str(random.randint(1, 14))
    file_id = cached_ids.get(roll_result)
    
    if file_id:
        media = types.InputMediaAnimation(media=file_id, caption="Here is Taher!")
        try:
            bot.edit_message_media(media=media, inline_message_id=call.inline_message_id)
            bot.answer_callback_query(call.id, "Revealed!")
        except Exception:
            pass

# --- 8. Start Everything ---
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print("Bot is starting...")
    bot.infinity_polling()
