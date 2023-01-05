# Bitbust

A Escape From Tarkov oriented Twitch Bit integration.


## Usage

```
1. Download BitBustStarter.exe
2. Run this and follow the prompted instructions
    * The first time you run it the program will terminate after creating a list of prices
    * Simply relaunch after changing the prices
3. Ensure the channel name is correct. It will then prompt you to authenticate with Twith
    * This will as for READ access, meaning it can only read chat, not send messages or moderate chat
4. The program should inform you that it has joined chat
    * If anything happens please attach your log.txt in an issue
```


If you wish to build this program from source make sure that you have all needed PyPip packages and either run as a standard python program, or use PyInstaller to build it using this command:
```
pyinstaller --win-private-assemblies --hidden-import=pywintypes --noconfirm --icon 'icon.png'  --add-data 'slots/*;slots' -D .\BitBust.py
```
Before building you must change `APP_ID` and `APP_SECRET` in BitBust.py. See https://dev.twitch.tv for instructions on how to register an **application.**

## Rewards

I feel most of the reward names are pretty self explanatory, so here is a list.

```
    "drop_primary": 1,
    "drop_secondary": 2,
    "drop_pistol": 3,
    "drop_armor": 4,
    "drop_all_weapons": 5,
    "drop_all_wearable": 6,
    "drop_rig": 7,
    "drop_backpack": 8,
    "rotate_10_sec": 9, # Rotates the screen 180 degrees (upside down)
    "walk_forward_10_sec": 10, # Holds W for 10 seconds
    "ensure_inventory_closed_5": 11, # Will exit the inventory for 5 seconds
    "ensure_inventory_open_5": 12, # Will have the inventory open for 5 seconds
    "shoot_sub": 0, # A placeholder for a sub rewards, will shoot on a sub
    "shoot": 14, # A simpl shoot
    "disable_mouse_10_sec": 15, # Disables mouse input for 10 seconds
    "disable_keyboard_10_sec": 16 # Disables keyboard input for 10 seconds
```

## Configuration

There is little configuration needed to run the program. The only thing to do is changing the prices located in "BitBustPrices.json"

Set the numeric value after the colon to the desired bit value, make sure that there are no duplicate rewards numbers. If you wish to `disable` an action completly set it to -1 (shoot_sub should be left at 0 if you want it enabled)


## Disclaimer

This project was thrown together in a short amount of time and may not always function as intended. With the testing done live on twitch.tv/sterdekie it appears to work, but I am not responsible if the program mis-behaves.
