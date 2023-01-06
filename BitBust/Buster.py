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
from pynput import keyboard, mouse



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
            "shoot": self.shoot,
            "disable_mouse_10_sec": self.disable_mouse_10_seconds,
            "disable_keyboard_10_sec": self.disable_keyboard_10_seconds,
        }
        
        self.running = True
        self.active = False

        self.ensure_inventory_open = False
        self.ensure_inventory_close = False


        self.buster_main_loop = None
        self.in_raid = False
        self.inventory_is_open = False
        self.inventory_tab_is_open = False
        self.tarkov_is_active = False

        self.write_lock = asyncio.Lock()
        self.action_lock = asyncio.Lock()
        self.execute_lock = asyncio.Lock()
        self.action_queue = []
        
        self.mouse_blocker = None
        self.kbd_blocker = None
        self.suppress_keyboard_mouse = False
        
        self.disabled_keys = []
        
        self.last_kbdmouse_disabled_at = 0
        
        
        # Variables for ensuring that the different tasks are running
        self.inventory_task_last_run = time.time()
        self.tarkov_task_last_run = time.time()
        self.in_raid_task_last_run = time.time()
        self.main_task_last_run = time.time()




    def __enable_mouse_and_keyboard(self):
        if self.kbd_blocker:
            self.kbd_blocker._suppress = False
        if self.mouse_blocker:
            self.mouse_blocker._suppress = False
        
    def __disable_mouse_and_keyboard(self):
        if self.suppress_keyboard_mouse:
            if self.kbd_blocker:
                self.kbd_blocker._suppress = True
            if self.mouse_blocker:
                self.mouse_blocker._suppress = True


    async def disable_mouse_and_keyboard(self, block_mouse=True, block_keyboard=True):
        await self.write_to_file("Disabling mouse and keyboard")
        self.suppress_keyboard_mouse = True
        
        if self.mouse_blocker:
            self.mouse_blocker.stop()
            self.mouse_blocker = None
            await self.write_to_file("Stopping mouse blocker thread", print_to_console=False)
            
        if self.kbd_blocker:
            self.kbd_blocker.stop()
            self.kbd_blocker = None
            await self.write_to_file("Stopping kybd blocker thread", print_to_console=False)
        if block_mouse:
            self.mouse_blocker = mouse.Listener(suppress=True)
            self.mouse_blocker.start()
            await self.write_to_file("Starting mouse blocker thread", print_to_console=False)
        if block_keyboard:
            self.kbd_blocker = keyboard.Listener(suppress=True)
            keys_to_releasse = [0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x10, 0x11, 0x12, 0x5B, 0x1B, 0x09]
            for key in keys_to_releasse:
                win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
            self.kbd_blocker.start()
            await self.write_to_file("Starting keyboard blocker thread", print_to_console=False)
        self.last_kbdmouse_disabled_at = time.time()
        await asyncio.sleep(0.05)


        
        
    async def enable_mouse_and_keyboard(self):
        await self.write_to_file("Enabling mouse and keyboard")
        self.suppress_keyboard_mouse = False
        

        
        if self.mouse_blocker:
            await self.write_to_file("Stopping mouse blocker thread", print_to_console=False)
            self.mouse_blocker.stop()
            self.mouse_blocker = None
        if self.kbd_blocker:
            await self.write_to_file("Stopping keyboard blocker thread", print_to_console=False)
            self.kbd_blocker.stop()
            self.kbd_blocker = None
            
            # Send a "release" event for all keys in 
            # use win32api to send key up events for all keys
            # a,b,c,d,e ... + shift, ctrl, alt, win, esc, tab etc
            keys_to_releasse = [0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x10, 0x11, 0x12, 0x5B, 0x1B, 0x09]
            for key in keys_to_releasse:
                win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
        
            
    def call_threadsafe_parse_action(self, action: str):
        asyncio.run_coroutine_threadsafe(self.parse_action(action), self.buster_main_loop)


    async def parse_action(self, action: str):
        if action in self.rewards:
            # Create single action
            a = SingleAction(self.rewards[action], [], self, action)
            if action == "rotate_10_sec":
                a.args.append("force")
                
            await self.write_to_file(f"Queing action {action}")
            await self.queue_action(a)
        else:
            await self.write_to_file(f"Action {action} does not exist")


    def thread_safe_write_to_file(self, data: str, print_to_console: bool = True):
        asyncio.run_coroutine_threadsafe(self.write_to_file(data, print_to_console), self.buster_main_loop)

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
        except Exception as e:
            await self.write_to_file(f"Failed to rotate screen because {e}")
        finally:
            screen.rotate_to(current_orientation)


    # Will queue an action to be executed when tarkov is the active window
    # do not run multiple of these at the same time
    async def queue_action(self, action):
        async with self.action_lock:
            await self.write_to_file("Queued action")
            self.action_queue.append(action)
            # print(self.action_queue)
                
    async def drop_item(self, item):
        tries = 0
        while not self.inventory_is_open and self.inventory_tab_is_open:
            await asyncio.sleep(0.05)
            tries += 1
            if tries > 25:
                await self.write_to_file(f"Failed to drop item {item} because inventory was not open")
                return False
            
        try:
            dropped = False
            tries = 0
            while not dropped: 
                tries += 1
                if tries > 25:
                    await self.write_to_file(f"Failed to drop item {item} because inventory was not open")
                    return False
                
                await asyncio.sleep(0.1)
                if not self.ensure_inventory_open: raise Exception("Inventory is not ensured") 
                if not self.inventory_is_open or not self.inventory_tab_is_open: continue
                loc = LocationValues.SLOT_ABSOLUTE_POSITIONS[item]          
                
                pyautogui.moveTo(loc[0], loc[1], 0, pyautogui.easeInOutQuad)

                self.__enable_mouse_and_keyboard()
                pyautogui.press('delete')
                self.__disable_mouse_and_keyboard()
                # wait since we want to check if inventory was closed
                await asyncio.sleep(0.05)
                if not self.inventory_is_open or not self.inventory_tab_is_open: continue
                dropped = True
                
                
                
            # Realease the cursor
        except Exception as e:
            await self.write_to_file(f"Failed to drop item {item} because {e}")
            return False
        finally:
            await self.write_to_file(f"Dropped item {item}")

        return True        
            
    
    async def scroll_inventory(self):
        tries = 0
        while not self.inventory_is_open and not self.inventory_tab_is_open:
            await asyncio.sleep(0.05)
            tries += 1
            if tries > 20:
                await self.write_to_file(f"Failed to scroll inventory because inventory was not open")
                return False
        try:
            loc = LocationValues.SLOT_ABSOLUTE_POSITIONS["INVENTORY"]
            pyautogui.moveTo(loc[0], loc[1], 0, pyautogui.easeInOutQuad)


            for _ in range(10):
                win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, 25, 0)
                await asyncio.sleep(0.005)
        finally:
            pass
            

    async def shoot(self):
        await self.write_to_file("Shooting")
        if self.inventory_is_open:
            self.ensure_inventory_close = True
            await asyncio.sleep(0.1)
        else:
            self.ensure_inventory_close = True
        pyautogui.click(button='left')
        self.ensure_inventory_close = False
        


    async def drop_primary(self):
        self.ensure_inventory_open = True
        await self.disable_mouse_and_keyboard()
        await self.write_to_file(f"Dropping primary: {self.inventory_is_open} {self.ensure_inventory_open}")
        await self.drop_item("PRIMARY")
        await self.enable_mouse_and_keyboard()
        self.ensure_inventory_open = False
        await self.close_inventory()

    async def drop_secondary(self):
        self.ensure_inventory_open = True
        await self.disable_mouse_and_keyboard()
        await self.write_to_file(f"Dropping secondary: {self.inventory_is_open} {self.ensure_inventory_open}")
        await self.drop_item("SECONDARY")
        await self.enable_mouse_and_keyboard()
        self.ensure_inventory_open = False
        await self.close_inventory()

    async def drop_pistol(self):
        self.ensure_inventory_open = True
        await self.disable_mouse_and_keyboard()
        await self.write_to_file(f"Dropping pistol: {self.inventory_is_open} {self.ensure_inventory_open}")
        await self.drop_item("PISTOL")
        await self.enable_mouse_and_keyboard()
        self.ensure_inventory_open = False
        await self.close_inventory()

    async def drop_armor(self):
        self.ensure_inventory_open = True
        await self.disable_mouse_and_keyboard()
        await self.write_to_file(f"Dropping armor: {self.inventory_is_open} {self.ensure_inventory_open}")
        await self.drop_item("ARMOR")
        await self.enable_mouse_and_keyboard()
        self.ensure_inventory_open = False
        await self.close_inventory()
        
    async def drop_all_weapons(self):
        self.ensure_inventory_open = True
        await self.disable_mouse_and_keyboard()
        await self.write_to_file(f"Dropping all weapons: {self.inventory_is_open} {self.ensure_inventory_open}")
        await self.drop_item("PISTOL")
        await self.drop_item("SECONDARY")
        await self.drop_item("PRIMARY")
        await self.enable_mouse_and_keyboard()
        self.ensure_inventory_open = False
        await self.close_inventory()
        await asyncio.sleep(0.5)
        

        
        
    
    async def drop_rig(self):
        self.ensure_inventory_open = True
        await self.disable_mouse_and_keyboard()
        await self.write_to_file(f"Dropping rig: {self.inventory_is_open} {self.ensure_inventory_open}")
        await self.scroll_inventory()
        await self.drop_item("RIG")
        await self.enable_mouse_and_keyboard()
        self.ensure_inventory_open = False
        await self.close_inventory()

    async def drop_backpack(self):
        self.ensure_inventory_open = True
        await self.disable_mouse_and_keyboard()
        await self.write_to_file(f"Dropping backpack: {self.inventory_is_open} {self.ensure_inventory_open}")
        await self.scroll_inventory()
        await self.drop_item("BACKPACK")
        await self.enable_mouse_and_keyboard()
        self.ensure_inventory_open = False
        await self.close_inventory()
        
        
    async def drop_all_wearable(self):
        # win32api press v
        win32api.keybd_event(0x56, 0, 0, 0)
        await self.disable_mouse_and_keyboard()
        await self.write_to_file(f"Dropping all wearable: {self.inventory_is_open} {self.ensure_inventory_open}")
        await asyncio.sleep(0.5)
        
        self.ensure_inventory_open = True
        
        await self.drop_item("HEADWEAR")
        await self.drop_item("FACECOVER")
        await self.drop_item("HEADPHONE")
        await self.drop_item("ARMOR")
        await self.scroll_inventory()
        await self.drop_item("RIG")
        await self.drop_item("BACKPACK")
        
        await self.enable_mouse_and_keyboard()
        
        self.ensure_inventory_open = False
        await self.close_inventory()
        await asyncio.sleep(0.7)
        
            
    async def walk_forward(self, duration=10):
        start_time = time.time()
        self.ensure_inventory_close = True
        await self.write_to_file(f"walking forward")
        while time.time() - start_time < duration:
            await asyncio.sleep(0.001)
            if self.inventory_is_open:
                continue
            pyautogui.keyDown('w')
        pyautogui.keyUp('w')
        self.ensure_inventory_close = False
            
            
    async def ensure_inventory_closed_5(self, duration=5):
        self.ensure_inventory_close = True
        await self.write_to_file(f"ensuring inventory closed")
        await asyncio.sleep(duration)
        self.ensure_inventory_close = False
    

    async def ensure_inventory_open_5(self, duration=5):
        # Ensure inventory is open for 1 second
        self.ensure_inventory_open = True
        await self.write_to_file(f"ensuring inventory open")
        await asyncio.sleep(duration)
        self.ensure_inventory_open = False


    async def disable_keyboard_10_seconds(self):
        await self.disable_mouse_and_keyboard(block_mouse=False, block_keyboard=True)
        await asyncio.sleep(10)
        await self.enable_mouse_and_keyboard()
        
    async def disable_mouse_10_seconds(self):
        await self.disable_mouse_and_keyboard(block_mouse=True, block_keyboard=False)
        await asyncio.sleep(10)
        await self.enable_mouse_and_keyboard()
        
    
    async def close_inventory(self):
        if self.inventory_is_open:
            pyautogui.press('tab')


    async def disable_kbd_mouse_check(self):
        # Will ensure that we do not disable the mouse and keyboard in certain states
        if ((not self.active) or (not self.tarkov_is_active) or (not self.suppress_keyboard_mouse)):
            if self.kbd_blocker or self.mouse_blocker:
                await self.enable_mouse_and_keyboard()
                await self.write_to_file(f"Main: Disabled mouse and keyboard, but not in a state to do so, re-enabling", print_to_console=False)
                return
                
        # Ensure that the mouse and keyboard is not disabled for more than 15 seconds
        if self.kbd_blocker or self.mouse_blocker:
            if time.time() - self.last_kbdmouse_disabled_at > 15:
                await self.write_to_file(f"Main: Disabled mouse and keyboard for more than 15 seconds, re-enabling", print_to_console=False)
                await self.enable_mouse_and_keyboard()


    async def main_loop(self):
        await self.write_to_file(f"Main loop started")
        last_action = None
        last_log = 0
        while self.running:
            self.main_task_last_run = time.time()
            # Log every 10 seconds
            if time.time() - last_log > 10:
                await self.write_to_file(f"Main: Tasks in Q: {len(self.action_queue)}, Active: {self.active}, Tarkov Active: {self.tarkov_is_active}, Inventory: {self.inventory_is_open}, Ensure Open: {self.ensure_inventory_open}", print_to_console=False)
                last_log = time.time()
            try:
                await self.disable_kbd_mouse_check()
                
                if not self.active:
                    await asyncio.sleep(0.5)
                    continue
                
                action = None
                async with self.action_lock:
                    if len(self.action_queue) > 0 and (not last_action or last_action.done()):
                        action = self.action_queue.pop(0)
                        await self.write_to_file(f"Popping action {action}")
                
                    if action: 
                        new_loop = asyncio.get_event_loop()
                        await self.write_to_file(f"Executing action {action}")
                        last_action = new_loop.create_task(action.execute())
                await asyncio.sleep(0.05)
            except Exception as e:
                # Log the current states
                await self.write_to_file(f"Failed to execute action because {e}")
                await self.write_to_file(f" Active: {self.active}, Tarkov Active: {self.tarkov_is_active}, Inventory: {self.inventory_is_open}, Ensure Open: {self.ensure_inventory_open}")
        
        await self.enable_mouse_and_keyboard()
        await self.write_to_file(f"Main loop ended")
                
                
    async def check_tarkov_task(self):
        await self.write_to_file(f"Starting tarkov checker")
        last_log = 0
        while self.running:
            try:
                self.tarkov_task_last_run = time.time()
                # Log to file once every 5 seconds
                if time.time() - last_log > 2:
                    last_log = time.time()
                    await self.write_to_file(f"INFO: Tarkov checker is running, active: {self.active}, tarkov active: {self.tarkov_is_active}", print_to_console=False)
                    
                    
                self.tarkov_is_active = pyautogui.getActiveWindowTitle() == "EscapeFromTarkov"
                await asyncio.sleep(0.01)
            except Exception as e:
                await self.write_to_file(f"Failed to check tarkov because {e}")
                await asyncio.sleep(0.1)
        await self.write_to_file(f"Exiting tarkov checker")
            
    async def check_in_raid_task(self):
        await self.write_to_file(f"Starting in raid checker")
        last_log = 0
        while self.running:
            try:
                # Log to file once every 5 seconds
                self.in_raid_task_last_run = time.time()
                if time.time() - last_log > 5:
                    last_log = time.time()
                    await self.write_to_file(f"INFO: In-raid checker is running, active: {self.active}, in raid: {self.in_raid}", print_to_console=False)
                
                if self.tarkov_is_active:
                    self.in_raid = not (bool(pyautogui.locateOnScreen('slots/settings.png', region=LocationValues.SETTINGS, confidence=0.7)) or\
                        bool(pyautogui.locateOnScreen('slots/main_menu.png', region=LocationValues.MAIN_MENU, confidence=0.7)))
                else:
                    self.in_raid = False
                await asyncio.sleep(0.1)
            except Exception as e:
                await self.write_to_file(f"Failed to check in raid because {e}")
                await asyncio.sleep(0.1)
        await self.write_to_file("In-raid checker stopped")
            
            
    async def check_inv_task(self):
        await self.write_to_file("Starting inventory checker")
        last_log = 0
        last = 0
        while self.running:
            try:
                await asyncio.sleep(0.001)
                # Log to file once every 5 seconds
                cur = time.time()
                self.inventory_task_last_run = cur
                if cur - last_log > 5:
                    last_log = time.time()
                    await self.write_to_file(f"INFO: Inventory checker is running, active: {self.active}, inv open: {self.inventory_is_open}, ensure open: {self.ensure_inventory_open}, ensure closed: {self.ensure_inventory_close}", print_to_console=False)
                
                if cur - last < 0.05:  
                    await asyncio.sleep(0.01 - (cur - last))
                if not self.tarkov_is_active:
                    self.ensure_inventory_close = False
                    self.ensure_inventory_open = False
                    await asyncio.sleep(0.1)
                else:
                    self.inventory_is_open = \
                        bool(pyautogui.locateOnScreen('slots/INV_CHECK.png', 
                            region=LocationValues.INVENTORY_CHECK_LOC,
                            confidence=0.7))
                    
                    # if on another tab
                    if not self.inventory_is_open:
                        px = pyautogui.pixel(252,14)
                        self.inventory_is_open = px == (54,63,79)
                        
                    # Ensure inventory is in the correct state
                    try:
                        px = pyautogui.pixel(160, 9)
                        self.inventory_tab_is_open =  px == (255, 255, 255)
                            
                        # if inverory is open, but inv tab is not selected, select it
                        if self.tarkov_is_active and self.ensure_inventory_open and self.inventory_is_open and not self.inventory_tab_is_open:
                            await self.write_to_file("Ensuring inventory tab is selected")
                            if self.mouse_blocker:
                                self.mouse_blocker._suppress = False
                            await asyncio.sleep(0.008)
                            pyautogui.moveTo(219,21, 0)
                            pyautogui.click()
                            await asyncio.sleep(0.01)
                            self.__disable_mouse_and_keyboard()
                        
                        
                        
                        if self.tarkov_is_active and self.ensure_inventory_open and not self.inventory_is_open:
                            await self.write_to_file("Ensuring inventory is open")
                            
                            self.__enable_mouse_and_keyboard()
                            pyautogui.press('tab')
                            self.__disable_mouse_and_keyboard()
                            if self.mouse_blocker:
                                self.mouse_blocker._suppress = False
                            await asyncio.sleep(0.005)
                            pyautogui.moveTo(219,21, 0)
                            pyautogui.click()                            
                            await asyncio.sleep(0.01)
                            self.__disable_mouse_and_keyboard()
                            
                            px = pyautogui.pixel(160, 9)
                            self.inventory_tab_is_open =  px == (255, 255, 255)
                                
                            # if inverory is open, but inv tab is not selected, select it
                            if self.tarkov_is_active and self.ensure_inventory_open and self.inventory_is_open and not self.inventory_tab_is_open:
                                await self.write_to_file("Ensuring inventory tab is selected")
                                if self.mouse_blocker:
                                    self.mouse_blocker._suppress = False
                                await asyncio.sleep(0.005)
                                pyautogui.moveTo(219,21, 0)
                                pyautogui.click()
                                await asyncio.sleep(0.01)
                                self.__disable_mouse_and_keyboard()
                        
                    except Exception as e:
                        await self.write_to_file(f"Failed to open inventory because {e}")
                    finally:
                        pass
                        
                    # Ensure open has priority over ensure close
                    if (not self.ensure_inventory_open) and self.tarkov_is_active and self.ensure_inventory_close and self.inventory_is_open:
                        await self.write_to_file("Ensuring inventory is closed")
                        pyautogui.press('tab')
                        await asyncio.sleep(0.01)
                    
                last = time.time()
            except Exception as e:
                await self.write_to_file(f"UNCAUGHT: Failed to check inventory because {e}", print_to_console=False)
                await asyncio.sleep(0.1)
        await self.write_to_file("Stopping inventory checker")
                

                        
    def start(self):
        self.running = True
        self.active = True
        f1 = asyncio.ensure_future(self.main_loop())
        f2 = asyncio.ensure_future(self.check_tarkov_task())
        f3 = asyncio.ensure_future(self.check_inv_task())
        f4 = asyncio.ensure_future(self.check_in_raid_task())
        self.buster_main_loop = asyncio.get_event_loop()
        return [f1, f2, f3, f4]
                
    def disable(self):
        self.active = False
        
    def enable(self):
        self.active = True
        
    def stop(self):
        print("Stopping")
        self.running = False
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
    
