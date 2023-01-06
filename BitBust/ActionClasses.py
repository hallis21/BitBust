import asyncio
from typing import List


class SingleAction:
    def __init__(self, action, args, buster, name):
        self.action = action
        self.args = args
        self.buster = buster
        self.name = name
        
        
    async def __stop_execute(self):
        self.buster.ensure_inventory_open = False
        self.buster.ensure_inventory_close = False
        await self.buster.enable_mouse_and_keyboard()
    
    def __str__(self):
        return self.name
        
    async def execute(self):
        t = None
        async with self.buster.execute_lock:
            if len(self.args) > 0 and self.args[0] == "force":
                t :asyncio.Future = asyncio.ensure_future(self.action())
            if t:
                while not t.done():
                    await asyncio.sleep(0.05)
                return
            
            if self.buster.tarkov_is_active and self.buster.in_raid:
                t :asyncio.Future = asyncio.ensure_future(self.action(*self.args))
            else:
                await self.__stop_execute()
                await self.buster.write_to_file(f"Tarkov is not active, not executing action, ({self.buster.tarkov_is_active}, {self.buster.in_raid})")
                
            if t:
                while not t.done():
                    if not self.buster.tarkov_is_active and self.buster.in_raid:
                        t.cancel()  
                        await self.__stop_execute()
                        await self.buster.write_to_file("Tarkov is not active or not in raid, cancelling action")
                        break
                    await asyncio.sleep(0.01)
            await self.buster.write_to_file(f"Action {self.name} finished executing")
            await self.__stop_execute()
            await asyncio.sleep(0.1)


class CompoundAction:
    def __init__(self, actions: List[SingleAction], buster):
        self.actions = actions
    async def execute(self):
        to_await = []
        for action in self.actions:
            # Do not await, we want to execute all at the same time
                to_await.append(action.execute())
        await asyncio.gather(*to_await)