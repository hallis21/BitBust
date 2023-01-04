from time import sleep
from pynput import keyboard, mouse


supp = False
def keyboard_listener():
    global key
    global keyboard_listener

    def on_press(key):
        pass

    def on_release(key):
        pass

    def win32_event_filter(msg, data):
        
        if not supp:
            listener._suppress = False
        else:
            listener._suppress = True        
        return True

    return  keyboard.Listener(
        on_press=on_press, 
        on_release=on_release, 
        win32_event_filter=win32_event_filter,
        suppress=False
    )


listener = mouse.Listener()

if __name__== '__main__':
    with listener as ml:
        listener._suppress = True
        sleep(2)
        listener._suppress = False
        sleep(2)
