import json
import os
import sys
from time import sleep
import time
import requests
from twitchAPI import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
from Buster import Buster
import threading
from playsound import playsound
import msvcrt



APP_ID = 'hkcijalj81uknodvvlzs1q5ki5pzov'
APP_SECRET = "hidden"
USER_SCOPE = [AuthScope.CHAT_READ]

# if "target_channel.txt" exists, use this as the target channel
TARGET_CHANNEL = ""


import signal
bust = Buster()

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)
    
    
  def exit_gracefully(self, *args):
    bust.enable_mouse_and_keyboard()
    self.kill_now = True



busted = False
bust_thread = None

prices = {}
normal_prices = {}
admins = []
last_restarted = 0

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
    if msg.bits > 0:
        if msg.bits in prices:
            if bust:
                print(f"Executing action from {msg.user.name} for {msg.bits} bits ({prices[str(msg.bits)]})")
                await bust.parse_action(prices[str(msg.bits)])

async def backdoor_slut(cmd: ChatCommand):
    param = cmd.parameter.split(" ")
    if len(param) < 0:
        return
    param = param[0]
    if param in prices:
        param = prices[param]
    
    if cmd.user.name.lower() == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL or  cmd.user.name.lower() in admins:
        try:
            if param in normal_prices: 
                await bust.parse_action(param)
            
        except:
            pass
    else:
        if param not in normal_prices:
            return
        # Load "balance.json" from the folder one level up
        try:
            if not os.path.exists('../balance.json'):
                with open('../balance.json', 'w+') as f:
                    json.dump({"tmp":{}}, f)
                
            
            balance = {}
            with open('../balance.json', 'r') as f:
                balance = json.load(f)
                if cmd.user.name.lower() in balance:
                    if param in balance[cmd.user.name.lower()]:
                        if balance[cmd.user.name.lower()][param] > 0:
                            await bust.parse_action(param)
                            balance[cmd.user.name.lower()][param] -= 1
                            
                        if balance[cmd.user.name.lower()][param] > 0:
                            del balance[cmd.user.name.lower()][param]
            with open('../balance.json', 'w') as f:   
                json.dump(balance, f)
                
                
        except Exception as e:
            print("Failed to read balance", e)
            return
            
            
async def add_balance(cmd: ChatCommand):
    try:
        param = cmd.parameter.split(" ")
        if len(param) < 2:
            return
        user = param[0]
        action = param[1]
        if action in prices:
            action = prices[action]
        
        
        if not (cmd.user.name.lower() == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL or cmd.user.name.lower() in admins):
            return
        if not os.path.exists('../balance.json'):
            print("Creating balance.json")
            with open('../balance.json', 'x') as f:
                json.dump({"placeholder":{}}, f)
        balance = {}
        with open('../balance.json', 'r') as f:
            user_to_add = user
            action_to_add = action
            if action_to_add not in normal_prices:
                print("Tried to add balance for invalid action: ", action_to_add)
                return
        
            balance = json.load(f)
            if user_to_add not in balance:
                balance[user_to_add] = {}
            if action_to_add not in balance[user_to_add]:
                balance[user_to_add][action_to_add] = 0
            balance[user_to_add][action_to_add] += 1

        with open('../balance.json', 'w') as f:   
            json.dump(balance, f)
        print("Added balance for ", user, action)
    except Exception as e:
        print("Failed to add balance", e)
        return
        
    

async def rotate(cmd: ChatCommand):
    if cmd.user.name.lower() == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL:
        try:
            await bust.rotate_screen(int(cmd.parameter))
        except:
            await bust.rotate_screen()

async def on_sub(sub: ChatSub):
    # Get price of "shoot"
        
    try:
        if "shoot_sub" in normal_prices:
            print(f"Shooting since {sub.chat.username} subbed!")
            await bust.parse_action("shoot")
    except Exception as e:
        print("Failed to shoot on sub", e)
        pass
    
    
async def restart_buster(cmd: ChatCommand, force=False):
    global busted
    if not (force or cmd.user.name.lower() == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL or cmd.user.name.lower() in admins):
        return
    
    print("Restarting BustBot")
    last_restarted = time.time()
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
    
async def after_all(cmd: ChatCommand):
    if not (cmd.user.name.lower() == 'hallis21'):
        return
    try:
        # Get absolute path to this cwd
        path = os.path.dirname(os.path.abspath(__file__)) 
        playsound(path+"\\slots\\afterall.mp3")
    except:
        pass
    
# add admin command
async def add_admin(cmd: ChatCommand):
    global admins
    if cmd.user.name.lower() == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL or cmd.user.name.lower() in admins:
        # Read admins from file
        admins = []
        try:
            with open('../admins.txt', 'r') as f:
                admins = f.read().splitlines()
        except:
            admins = []
        # Add admin to list
        if cmd.parameter.lower() not in admins:
            admins.append(cmd.parameter.lower())
            # Write admins to file
            with open('../admins.txt', 'w') as f:
                f.write("\n".join(admins))

async def rm_admin(cmd: ChatCommand):
    global admins
    if cmd.user.name.lower() == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL or cmd.user.name.lower() in admins:
        # Read admins from file
        admins = []
        try:
            with open('../admins.txt', 'r') as f:
                admins = f.read().splitlines()
        except:
            admins = []
        # Remove admin to list
        if cmd.parameter.lower() in admins:
            admins.remove(cmd.parameter.lower())
            # Write admins to file
            with open('../admins.txt', 'w') as f:
                f.write("\n".join(admins))

        
async def panic(cmd: ChatCommand):
    if cmd.user.name.lower() == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL or cmd.user.name.lower() in admins:
        # Forcefully exit the program
        print("Panic button pressed, exiting")
        # get current process and kill it
        os.kill(os.getpid(), signal.SIGTERM)


# async def dkm(cmd: ChatCommand):
#     if cmd.user.name.lower() == 'hallis21' or cmd.user.name.lower() == TARGET_CHANNEL or cmd.user.name.lower() in admins:
#         await bust.disable_mouse_and_keyboard()
#         await asyncio.sleep(20)
#         await bust.enable_mouse_and_keyboard()
    
async def run():
    global prices
    global normal_prices
    global last_restarted
    
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
    
    
    chat.register_command('daddyplease', backdoor_slut)
    chat.register_command('dp', backdoor_slut)
    chat.register_command('add_bust', add_balance)
    chat.register_command('add_bustlord', add_admin)
    chat.register_command('rm_bustlord', rm_admin)
    
    chat.register_command('rotate', rotate)
    chat.register_command('bbrestart', restart_buster)
    chat.register_command('afterall', after_all)
    chat.register_command('bbpanic', panic)
    # chat.register_command('dkm', dkm)
    
    
            
    # Read "prices.json" into a global dictionary
    with open('prices.json', 'r') as f:
        normal_prices = json.load(f)
        # invert to int:string
        prices = {str(v):k for k,v in normal_prices.items() if int(v) != -1}
    

    chat.start()
    killer = GracefulKiller()
    
    # Thread that waits for user input, calls bust.stop() when user presses enter

    try:
        # check killer if kill_now is true
        
        enters  = 0
        
        while not killer.kill_now:
            await asyncio.sleep(0.1)
            # Ensure that all tasks are running inside of Buster
            # 20 sec max downtime
            cur = time.time() - 20
            # wait 10 seconds before restarting again
            if last_restarted < cur+10:
                # Check if any of the tasks have been down for more than 20 seconds
                if (bust.main_task_last_run < cur) or (bust.tarkov_task_last_run < cur) or \
                    (bust.inventory_task_last_run < cur) or (bust.in_raid_task_last_run < cur):
                    print("Restarting Buster since it has been down for more than 20 seconds")
                    await restart_buster(None, force=True)
            
            
            if msvcrt.kbhit():
                if msvcrt.getch() == b'\r':
                    print("Hit enter again to stop BitBust")
                    enters += 1
            if enters >= 2:
                print("Exiting program")
                break
    finally:
        # now we can close the chat bot and the twitch api client
        chat.stop()
        await twitch.close()

# unsused for now
async def force_update():
    OWNER = "hallis21"
    REPO = "BitBust"
    API_ENDPOINT = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"

    # Set the API endpoint
    # Will update the application
    # Downloads the latest version from github
    # Unpacks it, copies prices.json and target_channel.txt to the folder
    # and then runs the new version with argument "delete_old"
    # The new version will then delete the old version and start

    
    # Get latest release from github
    r = requests.get(url = API_ENDPOINT)
    data = r.json()
    # Get the download url, find "BitBust.zip"
    download_url = ""
    for asset in data['assets']:
        if asset['name'] == "BitBust.zip":
            download_url = asset['browser_download_url']
            break
    if download_url == "":
        print("Could not find download url")
        return
    # Download the zip file
    r = requests.get(url = download_url)
    # Write the zip file to disk
    with open("BitBust.zip", "wb") as f:
        f.write(r.content)
    # Unpack the zip file to ../BitBust

if __name__ == '__main__':
    
    # Check if "balance.json" and "admins.txt" exists
    if not os.path.exists('../balance.json'):
        with open('../balance.json', 'w+') as f:
            json.dump({}, f)
    if not os.path.exists('../admins.txt'):
        with open('../admins.txt', 'w+') as f:
            f.write("hallis21")
    # read admins from file
    with open('../admins.txt', 'r') as f:
        admins = f.read().splitlines()
    
    
    
  
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
            "shoot": 14,
            "disable_mouse_10_sec": 15,
            "disable_keyboard_10_sec": 16
        }

        # Dump to file
        with open('prices.json', 'w+') as f:
            json.dump(t, f)
        print("No prices.json found. Created a new one. Please edit it and restart the script.")
        sleep(1)
    else:
        
        if os.path.exists('target_channel.txt'):
            with open('target_channel.txt', 'r') as f:
                TARGET_CHANNEL = f.read().strip()
        else:
            print("No target channel file found, please enter the channel name manually")
            TARGET_CHANNEL = input("Enter channel name: (dont fuck this up) ")
            print("Is this correct? (y/n) channel: ", TARGET_CHANNEL)
            if input().lower().strip() != "y":
                sys.exit(1) 
        
        
        
    
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
    