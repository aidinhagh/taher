import telebot
import random

# Initialize the bot
TOKEN = '8613689985:AAEeKxz5J6ankSRN2ufujQikg1UIkM8cGwY'
bot = telebot.TeleBot(TOKEN)

# Dictionary linking dice rolls (1-6) to specific GIF URLs
videos = {
    1: '1.mp4',
    2: '2.mp4',
    3: '3.mp4',
    4: '4.mp4',
    5: '5.mp4',
    6: '6.mp4',
    7: '7.mp4',
    8: '8.mp4',
    9: '9.mp4',
    10: '10.mp4',
    11: '11.mp4',
    12: '12.mp4',
    13: '13.mp4',
    15: '14.mp4',
}

# Listen for the /roll command
@bot.message_handler(commands=['roll'])
def send_roll_gif(message):
    # Pick a random number between 1 and 14
    roll_result = random.randint(1, 14)
    
    # Get the matching filename from your dictionary (e.g., 'silent_roll1.mp4')
    video_filename = videos.get(roll_result)
    
    # Reply to the user with their number
    bot.reply_to(message, f"You rolled a {roll_result}!")
    
    # Open the local file in 'rb' (read binary) mode and send it
    with open(video_filename, 'rb') as video_file:
        bot.send_animation(message.chat.id, video_file)

print("Bot is running...")
# Keep the bot running continuously
bot.infinity_polling()
