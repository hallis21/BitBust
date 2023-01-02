import asyncio
import os
from time import sleep
import time
from ActionClasses import SingleAction, CompoundAction
import win32api
import pyautogui
import rotatescreen
import win32con
import LocationValues



# State variables
class Buster:
    
    # Name:function
    
    def __init__(self):
        
        self.rewards = {
            "drop_primary": self.drop_primary,
            "drop_secondary": self.drop_secondary,
            "drop_pistol": self.drop_pistol,
            "drop_armor": self.drop_armor,
            "drop_all_weapons": self.drop_all_weapons,
            "drop_all_wearable": self.drop_all_wearable,
            "drop_rig":self.drop_rig,
            "drop_backpack": self.drop_backpack,
            "rotate_10_sec": self.rotate_screen,
            "walk_forward_10_sec": self.walk_forward,
            "ensure_inventory_closed_5": self.ensure_inventory_closed_5,
            "ensure_inventory_open_5": self.ensure_inventory_open_5,
            "shoot": self.shoot
        }
        
        self.running = True
        self.active = False

        self.ensure_inventory_open = False
        self.ensure_inventory_close = False

        self.in_raid = False
        self.inventory_is_open = False
        self.tarkov_is_active = False

        self.action_lock = asyncio.Lock()
        self.action_queue = []


        self.write_lock = asyncio.Lock()


    async def parse_action(self, action: str):
        if action in self.rewards:
            # Create single action
            a = SingleAction(self.rewards[action], [], self)
            if action == "rotate_10_sec":
                a.args.append("force")
                
            print("Queing action", action)
            await self.queue_action(a)
        else:
            await self.write_to_file(f"Action {action} does not exist")

    async def write_to_file(self, data: str, print_to_console: bool = True):
        # Append timestamp to log
        data = f"{int(time.time())} {data}"
        async with self.write_lock:
            # if file no exist, create it
            if not os.path.exists("log.txt"):
                with open("log.txt", "w+") as f:
                    f.write("")
            with open("log.txt", "a") as f:
                f.write(data)
                if print_to_console: print(data, end="\n" if data[-1] != "\n" else "")
                if data[-1] != "\n":
                    f.write("\n")


    async def rotate_screen(self, duration: float = 10):
        screen = rotatescreen.get_primary_display()
        current_orientation = screen.current_orientation
        try:
            if current_orientation == 180:
                screen.rotate_to(0)
            elif current_orientation == 0:
                screen.rotate_to(180)
            await asyncio.sleep(duration)
        finally:
            screen.rotate_to(current_orientation)


    # Will queue an action to be executed when tarkov is the active window
    # do not run multiple of these at the same time
    async def queue_action(self, action):
        async with self.action_lock:
            print("Queued action")
            self.action_queue.append(action)
                
    async def drop_item(self, item):
        tries = 0
        while not self.inventory_is_open:
            await asyncio.sleep(0.05)
            tries += 1
            if tries > 20:
                await self.write_to_file(f"Failed to drop item {item} because inventory was not open")
                return False
            
        try:
            dropped = False
            while not dropped: 
                await asyncio.sleep(0.001)
                if not self.ensure_inventory_open: raise Exception("Inventory is not ensured") 
                if not self.inventory_is_open: continue
                loc = LocationValues.SLOT_ABSOLUTE_POSITIONS[item]
                pyautogui.moveTo(loc[0], loc[1], 0, pyautogui.easeInOutQuad)
                # use clip cursor to lock the mouse to a certain area
                win32api.ClipCursor((0,0,0,0))
                win32api.ClipCursor((loc[0], loc[1], loc[0], loc[1]))
                
                pyautogui.press('delete')
                # wait since we want to check if inventory was closed
                await asyncio.sleep(0.05)
                if not self.inventory_is_open: continue
                dropped = True
            # Realease the cursor
        except Exception as e:
            await self.write_to_file(f"Failed to drop item {item} because {e}")
            return False
        finally:
            await self.write_to_file(f"Dropped item {item}")
            try:
                win32api.ClipCursor((0,0,1919,1079))
            except:
                pass
        return True        
            
    
    async def scroll_inventory(self):
        tries = 0
        while not self.inventory_is_open:
            await asyncio.sleep(0.05)
            tries += 1
            if tries > 20:
                await self.write_to_file(f"Failed to scroll inventory because inventory was not open")
                return False
        try:
            loc = LocationValues.SLOT_ABSOLUTE_POSITIONS["INVENTORY"]
            pyautogui.moveTo(loc[0], loc[1], 0, pyautogui.easeInOutQuad)
            win32api.ClipCursor((0,0,0,0))
            win32api.ClipCursor((loc[0], loc[1], loc[0], loc[1]))

            for _ in range(10):
                win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, 25, 0)
                await asyncio.sleep(0.005)
        finally:
            try:
                win32api.ClipCursor((0,0,1919,1079))
            except:
                pass
            

    async def shoot(self):
        if self.inventory_is_open:
            self.ensure_inventory_close = True
            await asyncio.sleep(0.01)
        else:
            self.ensure_inventory_close = True
        pyautogui.click(button='left')
        self.ensure_inventory_close = False
        


    async def drop_primary(self):
        self.ensure_inventory_open = True
        print(f"Dropping primary {self.inventory_is_open} {self.ensure_inventory_open}")
        await self.drop_item("PRIMARY")
        self.ensure_inventory_open = False
        await self.close_inventory()

    async def drop_secondary(self):
        self.ensure_inventory_open = True
        await self.drop_item("SECONDARY")
        self.ensure_inventory_open = False
        await self.close_inventory()

    async def drop_pistol(self):
        self.ensure_inventory_open = True
        await self.drop_item("PISTOL")
        self.ensure_inventory_open = False
        await self.close_inventory()

    async def drop_armor(self):
        self.ensure_inventory_open = True
        await self.drop_item("ARMOR")
        self.ensure_inventory_open = False
        await self.close_inventory()
        
    async def drop_all_weapons(self):
        self.ensure_inventory_open = True
        await self.drop_item("PISTOL")
        await self.drop_item("SECONDARY")
        await self.drop_item("PRIMARY")
        self.ensure_inventory_open = False
        await self.close_inventory()
        await asyncio.sleep(0.5)
        

        
        
    
    async def drop_rig(self):
        self.ensure_inventory_open = True
        await self.scroll_inventory()
        await self.drop_item("RIG")
        self.ensure_inventory_open = False
        await self.close_inventory()

    async def drop_backpack(self):
        self.ensure_inventory_open = True
        await self.scroll_inventory()
        await self.drop_item("BACKPACK")
        self.ensure_inventory_open = False
        await self.close_inventory()
        
        
    async def drop_all_wearable(self):
        # win32api press v
        win32api.keybd_event(0x56, 0, 0, 0)
        await asyncio.sleep(0.5)
        
        self.ensure_inventory_open = True
        
        await self.drop_item("ARMOR")
        await self.drop_item("HEADWEAR")
        await self.drop_item("FACECOVER")
        await self.drop_item("HEADPHONE")
        await self.scroll_inventory()
        await self.drop_item("RIG")
        await self.drop_item("BACKPACK")
        self.ensure_inventory_open = False
        await self.close_inventory()
        await asyncio.sleep(0.7)
        
    
            
    async def walk_forward(self, duration=10):
        start_time = time.time()
        self.ensure_inventory_closed = True
        while time.time() - start_time < duration:
            await asyncio.sleep(0.001)
            if self.inventory_is_open:
                continue
            pyautogui.press('w')
        self.ensure_inventory_closed = False
            
            
            
    async def ensure_inventory_closed_5(self, duration=5):
        self.ensure_inventory_closed = True
        await asyncio.sleep(duration)
        self.ensure_inventory_closed = False
    

    async def ensure_inventory_open_5(self, duration=5):
        # Ensure inventory is open for 1 second
        self.ensure_inventory_open = True
        await asyncio.sleep(duration)
        self.ensure_inventory_open = False


    async def close_inventory(self):
        if self.inventory_is_open:
            pyautogui.press('tab')





    async def main_loop(self):
        last_action = None
        while self.running:
            try:
                # await self.write_to_file(f" Active: {self.active}, Tarkov Active: {self.tarkov_is_active}, Inventory: {self.inventory_is_open}, Ensure Open: {self.ensure_inventory_open}", print_to_console=False)
                
                if not self.active:
                    await asyncio.sleep(0.5)
                    continue
                
                action = None
                async with self.action_lock:
                    if len(self.action_queue) > 0 and (not last_action or last_action.done()):
                        action = self.action_queue.pop(0)
                
                if action: 
                    new_loop = asyncio.get_event_loop()
                    last_action = new_loop.create_task(action.execute())
                await asyncio.sleep(0.05)
            except Exception as e:
                # Log the current states
                await self.write_to_file(f"Failed to execute action because {e}")
                await self.write_to_file(f" Active: {self.active}, Tarkov Active: {self.tarkov_is_active}, Inventory: {self.inventory_is_open}, Ensure Open: {self.ensure_inventory_open}")
                
                
                
    async def check_tarkov_task(self):
        while self.running:
            self.tarkov_is_active = pyautogui.getActiveWindowTitle() == "EscapeFromTarkov"
            await asyncio.sleep(0.01)
            
    async def check_in_raid_task(self):
        while self.running:
            if self.tarkov_is_active:
                self.in_raid = not (bool(pyautogui.locateOnScreen('slots/settings.png', region=LocationValues.SETTINGS, confidence=0.7)) or\
                    bool(pyautogui.locateOnScreen('slots/main_menu.png', region=LocationValues.MAIN_MENU, confidence=0.7)))
            else:
                self.in_raid = False
            await asyncio.sleep(0.1)
            
            
    async def check_inv_task(self):
        last = time.time()
        while self.running:
            await asyncio.sleep(0.001)
            cur = time.time()
            if cur - last < 0.05:  
                await asyncio.sleep(0.01 - (cur - last))
            if not self.tarkov_is_active:
                await asyncio.sleep(0.1)
            else:
                self.inventory_is_open = \
                    bool(pyautogui.locateOnScreen('slots/INV_CHECK.png', 
                        region=LocationValues.INVENTORY_CHECK_LOC,
                        confidence=0.7))
                    
                # Ensure inventory is in the correct state
                try:
                    if self.tarkov_is_active and self.ensure_inventory_open and not self.inventory_is_open:
                        print("Opening inventory")
                        pyautogui.press('tab')
                        await asyncio.sleep(0.005)
                        pyautogui.moveTo(219,21, 0)
                        win32api.ClipCursor((0,0,0,0))
                        win32api.ClipCursor((219-1,21-1, 219+1,21+1))
                        await asyncio.sleep(0.005)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        await asyncio.sleep(0.01)
                finally:
                    try:
                        win32api.ClipCursor((0,0,1919,1079))
                    except:
                        pass
                    
                # Ensure open has priority over ensure close
                if (not self.ensure_inventory_open) and self.tarkov_is_active and self.ensure_inventory_close and self.inventory_is_open:
                    pyautogui.press('tab')
                    await asyncio.sleep(0.01)
                
            last = time.time()
        print("Done checking inventory")
                

                        
    def start(self):
        f1 = asyncio.ensure_future(self.main_loop())
        f2 = asyncio.ensure_future(self.check_tarkov_task())
        f3 = asyncio.ensure_future(self.check_inv_task())
        f4 = asyncio.ensure_future(self.check_in_raid_task())
        return [f1, f2, f3, f4]
                
    def disable(self):
        self.active = False
        
    def enable(self):
        self.active = True
        
    def stop(self):
        self.running = False



if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    bust = Buster()
    
    tasks = bust.start()
    

    a = SingleAction(bust.drop_all_wearable, [], bust)
    # comp = CompoundAction([a, b], bust)
    bust.active = True
    bust.tarkov_is_active = True
        
        
    import threading
    # Thread that waits for user input, calls bust.stop() when user presses enter
    def wait_for_input():
        input("Say when.")
        bust.stop()
    threading.Thread(target=wait_for_input).start()

    
    asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
    
    # main()