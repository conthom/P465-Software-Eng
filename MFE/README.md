# Monster File Editor (MFE) for Angband - Group 18

This directory contains a Python-based monster browser for Angband that can be used as a standalone tool or integrated into the main Angband game.

## Files

- `edit_monsters.py`: The main Python script that displays the monster browser
- `run_monster_editor.sh`: Shell file for starting the edit monsters script but can also start with 
- `monster_screen.c`: C interface to integrate the browser with Angband
- `monster_screen.h`: Header file for the C interface
- `ui-game.c`: edited ui command Angband file for integrating ^M command for running the editor in game

Time spent:
Programming python curses pages and functionality: 3 hours
Debugging and fixing screen issues: 3 hours
Writing test cases: 1 hour
Testing app and making changes to code: 2 hours

Compared to our estimates we underestimated the amount of time spent programming and the amount of time it would take to debug some of the errors we encountered. We underestimated the amount of time it would take to understand saving and loading the monsters since its simpler than expected.

## Running as a Standalone Tool

You can run the monster browser as a standalone tool within the angband folder using:

```bash
 python3 src/MFE/edit_monsters.py
```

## Requirements

- Python 3.6 or higher
- Curses library for Python (usually included with Python)

## Notes

- The monster browser reads data directly from the `lib/gamedata/monster.txt` file
- The browser displays monster names in a list and shows detailed information when a monster is selected 

![img](mfe_pic.png)