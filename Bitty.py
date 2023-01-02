import json
import os
from time import sleep
from twitchAPI import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
from Buster import Buster
import threading


APP_ID = 'hkcijalj81uknodvvlzs1q5ki5pzov'
APP_SECRET = '***REMOVED***'
USER_SCOPE = [AuthScope.CHAT_READ]
TARGET_CHANNEL = 'sterdekie'

bust = None

prices = {}


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
            await bust.parse_action(prices[int(cmd.parameter)])
        except:
            pass

async def rotate(cmd: ChatCommand):
    if cmd.user.name == 'hallis21':
        try:
            await bust.rotate_screen(int(cmd.parameter))
        except:
            await bust.rotate_screen()
    
    
    
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
    
    chat.register_command('test', backdoor_slut)
    chat.register_command('rotate', rotate)
    
    
            
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
    
    if not os.path.exists('prices.json'):
        t = {
            "drop_primary":  55,
            "drop_secondary":  66,
            "drop_pistol":  77,
            "drop_armor":  88,
            "drop_all_weapons":  99,
            "drop_all_wearable":  111,
            "drop_rig": 122,
            "drop_backpack": 133
            }
        # Dump to file
        with open('prices.json', 'w+') as f:
            json.dump(t, f)
        print("No prices.json found. Created a new one. Please edit it and restart the script.")
        sleep(2)
    else:
    
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        bust = Buster()
        def start_buster():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tasks = bust.start()
            loop.run_until_complete(asyncio.wait(tasks))
            
        t = threading.Thread(target=start_buster)
        
        t.start()
        bust.enable()
        try:
            asyncio.run(run())
        finally:
            bust.stop()
            t.join()
    