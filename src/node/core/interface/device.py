import machine
import uasyncio as asyncio
from uasyncio import Event

from node.core.lib.primitives.pushbutton import Pushbutton
from node.core.interface.events import Events
import node.core.utils.fs as fs
from node.core.utils.logger import Log
import node.core.constants as constants

class Device(Events):
    _btn_pin = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)
    _btn_restart_duration = 5000

    def __init__(self, config):
        super().__init__()
        self.config = config
        # Event to wait for reset button
        self.__can_restart = Event()

    def set_config(self, config):
        # self.config["model"] = config["model"]
        self.config["ap"] = config
        fs.write(self.config)
    
    @property
    def is_setup(self):
        # Is setup if hub access point details are set
        return bool(self.config["ap"])

    async def restart(self, delay=None):
        Log.info("System.restart", "available: {0}, delay: {1}".format(self.__can_restart.is_set(), delay))
        await self.__can_restart.wait()
        if delay:
            await asyncio.sleep(delay)
        machine.reset()

    def __btn_action(self, down):
        if down == True:
            # Block ability to restart while btn down
            # (might be reset attempt)
            self.__can_restart.clear()
        else:
            # Free up restart on btn release
            self.__can_restart.set()


    def __btn_reset(self):
        # No need to reset up if not setup
        # if not self.is_setup:
        #     return

        self.event(constants.SYSTEM_RESET)
        fs.remove()
        self.__can_restart.set()
        asyncio.create_task(self.restart(5))
    
    async def routine(self):
        # Ability to restart available by default
        self.__can_restart.set()
        Pushbutton.long_press_ms = Device._btn_restart_duration
        pb = Pushbutton(Device._btn_pin)
        while True:
            pb.long_func(self.__btn_reset, ())
            pb.press_func(self.__btn_action, (True,))
            pb.release_func(self.__btn_action, (False,))
            await asyncio.sleep(60)


    
        
