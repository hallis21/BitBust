import asyncio
from time import sleep
import time
from typing import List

# State variables

running = True
active = False

ensure_inventory_open = False
ensure_inventory_close = False

inventory_is_open = False
tarkov_is_active = False

action_lock = asyncio.Lock()
action_queue = []


# Create a lock for writing to file
write_lock = asyncio.Lock()

async def write_to_file(data: str):
    # Append timestamp to log
    data = f"{int(time.time())} {data}"
    async with write_lock:
        with open("log.txt", "a") as f:
            f.write(data)
            print(data, end="\n" if data[-1] != "\n" else "")
            if data[-1] != "\n":
                f.write("\n")


# Defines an action
# The action can be compund, if they are they will be executed at the same time
# Example walk forward while shooting
class SingleAction:
    def __init__(self, action, args):
        self.action = action
        self.args = args
        
    async def execute(self):
        if tarkov_is_active:
            await self.action(*self.args)


class CompoundAction:
    def __init__(self, actions: List[SingleAction]):
        self.actions = actions
        
    async def execute(self):
        to_await = []
        for action in self.actions:
            # Do not await, we want to execute all at the same time
                to_await.append(action.execute())
        await asyncio.gather(*to_await)





# These will run on an interval to constantly check the states
# will update the variables above
async def tarkov_check():
    # TODO
    return True
async def inventory_check():
    # TODO
    return False
        

# Will queue an action to be executed when tarkov is the active window
# do not run multiple of these at the same time
async def queue_action(action):
    async with action_lock:
        action_queue.append(action)
        print("Queued action")
        

# Will drop one of the main items, weapons, armor, etc
async def drop_main_item(item):
    pass


async def drop_primary():
    pass

async def drop_secondary():
    pass


async def drop_pistol():
    pass

async def drop_armor():
    pass

async def press_key(key, duration):
    await asyncio.sleep(duration)
    print(f"Pressed {key} for {duration} seconds")

async def open_inventory():
    pass


async def close_inventory():
    pass


# Name:function
rewards = {
    "open_inventory": open_inventory, # Will ensure inv in this state 
    "close_inventory": close_inventory, # Will ensure inv in this state
    "primary": drop_primary,
    "secndary": drop_secondary,
    "pistol": drop_pistol,
    "armor": drop_armor
}



async def action_executor_task():
    print("lol")
    while running:
        if not active:
            await asyncio.sleep(0.5)
            continue
        async with action_lock:
            if len(action_queue) > 0:
                action = action_queue.pop(0)
                await action.execute()
            await asyncio.sleep(0.01)



# main
if __name__ == "__main__":
    
    event_loop = asyncio.new_event_loop()
    event_loop2 = asyncio.new_event_loop()
    # STart executor task, this is the main loop
    active = True
    executor_task = event_loop.create_task(action_executor_task())
    
    
    a = SingleAction(press_key, ["w", 1])
    event_loop.run_forever()
        
    # Wait for task to finish
    event_loop2.run_until_complete(queue_action(a))
    
    sleep(5)
    running = False
    # Wait for executor_task to finih, dont use await
    pass
