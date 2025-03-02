# Monster Front End (MFE) for Angband

This directory contains a Python-based monster browser for Angband that can be used as a standalone tool or integrated into the main Angband game.

## Files

- `show_monsters.py`: The main Python script that displays the monster browser
- `monster_screen.c`: C interface to integrate the browser with Angband
- `monster_screen.h`: Header file for the C interface

## Running as a Standalone Tool

You can run the monster browser as a standalone tool using:

```bash
python3 show_monsters.py
```

Or with curses-based UI:

```bash
python3 show_monsters.py --curses
```

To search for specific monsters:

```bash
python3 show_monsters.py --search "dragon"
```

## Integrating with Angband

To integrate the monster browser with Angband, follow these steps:

1. Add the following line to `src/ui-command.c` in the `do_cmd_knowledge()` function:

```c
#include "MFE/monster_screen.h"
```

2. Add a new option in the knowledge menu in the same file:

```c
/* In the do_cmd_knowledge() function, add: */
prt("m) Browse Monsters", y++, x);

/* In the switch statement, add: */
case 'm':
    do_cmd_monster_browser();
    break;
```

3. Add the monster_screen.c file to the build system:

   - For Makefile-based builds, add `monster_screen.o` to the OBJECTS list in `Makefile.src`
   - For CMake-based builds, add `src/MFE/monster_screen.c` to the source files list in `CMakeLists.txt`

4. Make sure Python 3 is installed on the system where Angband will run

## Requirements

- Python 3.6 or higher
- Curses library for Python (usually included with Python)

## Notes

- The monster browser reads data directly from the `lib/gamedata/monster.txt` file
- If the curses interface fails, it will fall back to a simpler text-based interface
- The browser displays monster names in a list and shows detailed information when a monster is selected 