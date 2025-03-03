# Monster File Editor (MFE) for Angband - Group 18

This directory contains a Python-based monster browser for Angband that can be used as a standalone tool or integrated into the main Angband game.

## Files

- `edit_monsters.py`: The main Python script that displays the monster browser
- `monster_screen.c`: C interface to integrate the browser with Angband
- `monster_screen.h`: Header file for the C interface
- `ui-game.c`: edited ui command c file for integrating ^M command for running the editor

Time spent:
Programming python curses pages and functionality: 6 hours (Connor)


## Running as a Standalone Tool

You can run the monster browser as a standalone tool using:
While the python file is within the angband src directory in the MFE folder.

```bash
python3 edit_monsters.py
```

## Integrating with Angband

To integrate the monster browser with Angband, follow these steps:


```c

2. Make sure Python 3 is installed on the system where Angband will run

Then run the command 
```
cd ~/CP465/angband2 && src/angband -dscreens=./lib/screens -dgamedata=./lib/gamedata -dhelp=./lib/help -dpref=./lib/customize -dfonts=./lib/fonts -dtiles=./lib/tiles -dsounds=./lib/sounds -dicons=./lib/icons
```
Within the angband directory
## Requirements

- Python 3.6 or higher
- Curses library for Python (usually included with Python)

## Notes

- The monster browser reads data directly from the `lib/gamedata/monster.txt` file
- The browser displays monster names in a list and shows detailed information when a monster is selected 