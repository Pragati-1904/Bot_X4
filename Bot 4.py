from telethon.sync import TelegramClient, events
from telethon.tl import types
import requests
import json
import asyncio


# Replace with your own values
API_ID = '6'
API_HASH = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
BOT_TOKEN =  '7558486828:AAE2QjJC3CHKCvi9rwwuA4YtMF7Cr0tR-8o'   #'6482350998:AAF05OkmabCsNPYr9me09exx4ij0svv6iVs'

admin_user_ids = [5645704474]

# Define your API key and API URL
#api_key = "2842e73e6ba0d1f033877d3dd6b994d6"
#api_url = "https://smmpanel.one/api/v2"

# SMMStone API credentials
api_key = 'b9d7981714649e36815ed17095d3fefd'
api_url = 'https://smmstone.com/api/v2'

#api_key = '0a4e84376a6ace254c9117dacd4a37c1'
#api_url = 'https://resellerprovider.ru/api/v2'

try:
    with open('channel_database.json', 'r') as file:
        channel_database = json.load(file)
except FileNotFoundError:
    channel_database = []

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
print("Bot is Online")

user_inputs = {}

def is_admin(event):
    return event.sender_id in admin_user_ids

@client.on(events.NewMessage)
async def handle_user_input(event):
    user_id = event.sender_id
    message = event.text

    if message == '/cancel':
        if user_id in user_inputs:
            del user_inputs[user_id]
            await event.reply("Process has been canceled.")
        else:
            await event.reply("No on-going process to cancel.")
        return  # Stop processing further commands

    #if user_id in ADMINS:

    if message.startswith('/add_channel'):
        if is_admin(event): 
              
            if user_id not in user_inputs:
                user_inputs[user_id] = {}
                user_inputs[user_id]['step'] = 'link'
                await event.reply("Let's start adding a channel details.\nPlease provide the channel link:")
                pass
        else:
            
            await event.reply("You are not authorized to use this command.")

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
        "service": '8416', #'4209',
        "link": link,
        "quantity": quantity,
        "runs": runs,
        "interval": interval
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        print(f"Request URL: {response.url}")
        print(f"Status Code: {response.status_code}")
        print(f"Raw Response: {response.text}")

        # Ensure response status code is OK
        response.raise_for_status()

        # Parse JSON response
        order_data = response.json()
        if "order" in order_data:
            return {"success": True, "order_id": order_data["order"]}
        else:
            return {"success": False, "error": "No 'order' key in response"}
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON. Raw response: {response.text}")
        return {"success": False, "error": "Invalid JSON response"}
                     


@client.on(events.NewMessage(incoming=True))
async def handle_new_post(event):
    for channel in channel_database:
        if channel.get('channel_id') == event.chat_id:
            if event.original_update.message:
                
                post_link = f"https://{channel['channel_link'][8:]}/{event.original_update.message.id}"
                print(f"New post in channel: {channel['channel_link']}")
                print(f"Post link: {post_link}")

                # Get parameters from channel_database
                service_id = "your_service_id"  # Replace with actual service ID
                quantity = channel['quantity']
                runs = channel['runs']
                interval = channel['interval']

                #await asyncio.sleep(5)

                #async def send_orders():
                for _ in range(runs):
                    order_result = await send_order(api_key, service_id, post_link, quantity, runs, interval)
                    if order_result.get("success"):
                        print(f"Order placed successfully. Order ID: {order_result['order_id']}")
                    else:
                        print(f"Failed to place order. Error: {order_result['error']}")
                    await asyncio.sleep(interval)  # Wait for the specified interval before sending the next order

@client.on(events.NewMessage)
async def handle_user_commands(event):
    user_id = event.sender_id
    message = event.message.text.lower()

    if message == '/orders':
        if is_admin(event):  # Check if the user is an admin
            orders_text = "Channel Orders:\n"
            for idx, channel in enumerate(channel_database, start=1):
                try:
                    orders_text += (
                        f"{idx}. Channel ID: {channel['channel_id']}\n"
                        f"   Channel Link: {channel['channel_link']}\n"
                        f"   Runs: {channel['runs']}\n"
                        f"   Interval: {channel['interval']} seconds\n"
                        f"   Quantity: {channel['quantity']}\n\n"
                    )
                except KeyError as e:
                    print(f"Error in channel data: {e}")    
            
            await event.reply(orders_text)
        else:
            await event.reply("You are not authorized to use this command.")
    
    elif message.startswith('/rem_channel'):
        if is_admin(event):  # Check if the user is an admin
            try:
                _, channel_idx = message.split(' ')
                channel_idx = int(channel_idx)
                if 1 <= channel_idx <= len(channel_database):
                    removed_channel = channel_database.pop(channel_idx - 1)
                    with open('channel_database.json', 'w') as file:
                        json.dump(channel_database, file, indent=4)
                    await event.reply(f"Channel ID {removed_channel['channel_id']} has been removed from the database.")
                else:
                    await event.reply("Invalid channel index. Please provide a valid index.")
            except ValueError:
                await event.reply("Invalid command format. Please use /rem_channel <index>.")
        else:
            await event.reply("You are not authorized to use this command.")

    elif message.startswith('/start'):
        await event.reply("Welcome to the View bot Server ! You can use the following commands:\n"
                          "/add_channel - Add a channel to the database\n"
                          "/orders - View channel orders\n"
                          "/rem_channel - Remove a channel from the database (Admins only)\n")
        return  # Stop processing further commands               
                
print("Bot is running...")
client.run_until_disconnected()
