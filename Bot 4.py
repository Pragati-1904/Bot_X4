from telethon.sync import TelegramClient, events
from telethon.tl import types
import requests
import json


# Replace with your own values
API_ID = '6'
API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
BOT_TOKEN = '6482350998:AAF05OkmabCsNPYr9me09exx4ij0svv6iVs'

# Define your API key and API URL
#api_key = "2842e73e6ba0d1f033877d3dd6b994d6"
#api_url = "https://smmpanel.one/api/v2"

# SMMStone API credentials
#api_key = 'd819a1f00c233199588f18d6b904216d'
#api_url = 'https://smmstone.com/api/v2'

# Yo Yo Media
api_key = 'd4f94ae6c43bdb0a08fd3237ebbb8e55d38a76e5c65995d1ab0a69b721deccfd'
api_url = 'https://yoyomedia.in/api/v2'


try:
    with open('channel_database.json', 'r') as file:
        channel_database = json.load(file)
except FileNotFoundError:
    channel_database = []

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
print("Bot is Online")

user_inputs = {}

@client.on(events.NewMessage)
async def handle_user_input(event):
    user_id = event.sender_id
    message = event.text
    
    if message.startswith('/add_channel'):
        if user_id not in user_inputs:
            user_inputs[user_id] = {}
            user_inputs[user_id]['step'] = 'link'
            await event.reply("Let's start adding a channel details.\nPlease provide the channel link:")

    elif user_id in user_inputs:
        current_step = user_inputs[user_id]['step']
        
        if current_step == 'link':
            if message.startswith('https://t.me/'):
                user_inputs[user_id]['link'] = message
                user_inputs[user_id]['step'] = 'channel_id'
                await event.reply("Please provide the channel ID:")
            else:
                await event.reply("Invalid channel link format. Please provide a valid link:")
        
        elif current_step == 'channel_id':
            try:
                channel_id = int(message)
                user_inputs[user_id]['channel_id'] = channel_id
                
                user_inputs[user_id]['step'] = 'runs'
                await event.reply("Please provide the number of runs:")
            except ValueError:
                await event.reply("Invalid channel ID format. Please provide a valid ID.")
            
            # Clear the user's input data
            #del user_inputs[user_id]
            
        elif current_step == 'runs':
            try:
                runs = int(message)
                user_inputs[user_id]['runs'] = runs
                
                user_inputs[user_id]['step'] = 'interval'
                await event.reply("Please provide the interval in minutes:")
            except ValueError:
                await event.reply("Invalid runs format. Please provide a valid number.")
            
        elif current_step == 'interval':
            try:
                interval = int(message)
                user_inputs[user_id]['interval'] = interval
                
                user_inputs[user_id]['step'] = 'quantity'
                await event.reply("Please provide the quantity:")
            except ValueError:
                await event.reply("Invalid interval format. Please provide a valid number.")
            
        elif current_step == 'quantity':
            try:
                quantity = int(message)
                user_inputs[user_id]['quantity'] = quantity
                
                # Store the completed entry in the channel_database
                channel_link = user_inputs[user_id]['link']
                channel_id = user_inputs[user_id]['channel_id']
                runs = user_inputs[user_id]['runs']
                interval = user_inputs[user_id]['interval']
                
                channel_database.append({
                    'channel_id': channel_id,
                    'channel_link': channel_link,
                    'runs': runs,
                    'interval': interval,
                    'quantity': quantity
                })
                
                with open('channel_database.json', 'w') as file:
                    json.dump(channel_database, file, indent=4)
                
                await event.reply(f"Channel details have been added to the database:\n"
                                  f"Channel ID: {channel_id}\n"
                                  f"Channel Link: {channel_link}\n"
                                  f"Runs: {runs}\n"
                                  f"Interval: {interval} minutes\n"
                                  f"Quantity: {quantity}")
            except ValueError:
                await event.reply("Invalid quantity format. Please provide a valid number.")
            
            # Clear the user's input data
            del user_inputs[user_id]   

async def send_order(api_key, service_id, link, quantity, runs, interval):
    params = {
        "key": api_key,
        "action": "add",
        "service": '169',
        "link": link,
        "quantity": quantity,
        "runs": runs,
        "interval": interval
    }
    
    # Send the API request
    response = requests.get(api_url, params=params)
    print(response)
    order_data = response.json()
    return order_data                 


@client.on(events.NewMessage(incoming=True))
async def handle_new_post(event):
    for channel in channel_database:
        if channel['channel_id'] == event.chat_id:
            if event.original_update.message:
                #post_link = f"https://t.me/{channel['channel_link'][8:]}/{event.original_update.message.id}"
                post_link = f"https://{channel['channel_link'][8:]}/{event.original_update.message.id}"
                print(f"New post in channel: {channel['channel_link']}")
                print(f"Post link: {post_link}")

                # Get parameters from channel_database
                service_id = "your_service_id"  # Replace with actual service ID
                quantity = channel['quantity']
                runs = channel['runs']
                interval = channel['interval']
                
                # Send order using the API
                order_data = await send_order(api_key, service_id, post_link, quantity, runs, interval)
                order_id = order_data.get('order')
                if order_id:
                    print(f"Order placed successfully. Order ID: {order_id}")
                else:
                    print("Failed to place order.")

print("Bot is running...")
client.run_until_disconnected()
