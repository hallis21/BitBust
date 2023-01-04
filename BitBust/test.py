from time import sleep
from pynput import keyboard, mouse

# disable mouse for 5 seconds
listener = mouse.Listener(suppress=True)
listener.start()
sleep(5)
listener.stop()
