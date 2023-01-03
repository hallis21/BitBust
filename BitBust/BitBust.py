import json
import os
import sys
from time import sleep
import time
from twitchAPI import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
from Buster import Buster
import threading



APP_ID = 'hkcijalj81uknodvvlzs1q5ki5pzov'
APP_SECRET = "hidden"
USER_SCOPE = [AuthScope.CHAT_READ]

# if "target_channel.txt" exists, use this as the target channel
TARGET_CHANNEL = ""
if os.path.exists('target_channel.txt'):
    with open('target_channel.txt', 'r') as f:
        TARGET_CHANNEL = f.read().strip()
else:
    print("No target channel file found, please enter the channel name manually")
    TARGET_CHANNEL = input("Enter channel name: (dont fuck this up) ")
    print("Is this correct? (y/n) channel: ", TARGET_CHANNEL)
    if input().lower().strip() != "y":
        sys.exit(1) 


bust = Buster()

busted = False
bust_thread = None

prices = {}


def start_buster():
    global busted
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = bust.start()
    loop.run_until_complete(asyncio.wait(tasks))
    busted = True



async def on_ready(ready_event: EventData):
    print('Bot starting up!')
    
    await ready_event.chat.join_room(TARGET_CHANNEL)
    print('Bot joined chat!')

async def on_message(msg: ChatMessage):
    # print(f"{msg.user.name}: {msg.text} (Bits {msg.bits})" )
    if msg.bits > 0:
        if msg.bits in prices:
            if bust:
                print(f"Executing action from {msg.user.name} for {msg.bits} bits ({prices[msg.bits]})")
                await bust.parse_action(prices[msg.bits])

async def backdoor_slut(cmd: ChatCommand):
    if cmd.user.name == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL:
        try:
            if prices[int(cmd.parameter)] == "shoot_sub":
                await bust.parse_action("shoot")
            else:
                await bust.parse_action(prices[int(cmd.parameter)])
        except:
            pass

async def rotate(cmd: ChatCommand):
    if cmd.user.name == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL:
        try:
            await bust.rotate_screen(int(cmd.parameter))
        except:
            await bust.rotate_screen()

async def on_sub(sub: ChatSub):
    # Get price of "shoot"
    try:
        if "shoot_sub" in prices.items():
            print(f"Shooting since {sub.chat.username} subbed!")
            await bust.parse_action("shoot")
    except:
        pass
    
    
async def restart_buster(cmd: ChatCommand):
    global busted
    print("Restarting BustBot")
    if not (cmd.user.name == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL):
        return
    
    bust.stop()
    time_started = time.time()
    while not busted and (time.time()-time_started) < 10:
        await asyncio.sleep(0.5)
    if not busted:
        print("Force restarting BustBot")
        bust_thread.join()
    busted = False
    bust_thread = threading.Thread(target=start_buster)
    bust_thread.start()

        
    
    
async def run():
    global prices
    
    # set up twitch api instance and add user authentication with some scopes
    twitch = await Twitch(APP_ID, APP_SECRET)
    auth = UserAuthenticator(twitch, USER_SCOPE)
    token, refresh_token = await auth.authenticate()
    await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)

    # create chat instance
    chat = await Chat(twitch)

    chat.register_event(ChatEvent.READY, on_ready)

    chat.register_event(ChatEvent.MESSAGE, on_message)
    
    chat.register_event(ChatEvent.SUB, on_sub)
    
    
    chat.register_command('test', backdoor_slut)
    chat.register_command('rotate', rotate)
    chat.register_command('bitbustrestart', restart_buster)
    
    
            
    # Read "prices.json" into a global dictionary
    with open('prices.json', 'r') as f:
        tmp_prices = json.load(f)
        # invert to int:string
        prices = {int(v):k for k,v in tmp_prices.items() if int(v) > 0}
    

    chat.start()
    
    # Thread that waits for user input, calls bust.stop() when user presses enter

    try:
        input('press ENTER to stop\n')
        input("Press Enter again to confirm\n")
    finally:
        # now we can close the chat bot and the twitch api client
        chat.stop()
        await twitch.close()

    
    

if __name__ == '__main__':
    
    # Bind "close window" button to call bust.stop() and t.join()
    

    
    
    
    
    
    if not os.path.exists('prices.json'):
        t = {
            "drop_primary":  1,
            "drop_secondary":  2,
            "drop_pistol":  3,
            "drop_armor":  4,
            "drop_all_weapons":  5,
            "drop_all_wearable":  6,
            "drop_rig": 7,
            "drop_backpack": 8,
            "rotate_10_sec": 9,
            "walk_forward_10_sec": 10,
            "ensure_inventory_closed_5": 11,
            "ensure_inventory_open_5": 12,
            "shoot_sub": 13,
            "shoot": 14
        }

        # Dump to file
        with open('prices.json', 'w+') as f:
            json.dump(t, f)
        print("No prices.json found. Created a new one. Please edit it and restart the script.")
        sleep(2)
    else:
    
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
            
        bust_thread = threading.Thread(target=start_buster)
        
        bust_thread.start()
        bust.enable()
        try:
            asyncio.run(run())
        finally:
            bust.stop()
            sleep(2)
            bust_thread.join()
    