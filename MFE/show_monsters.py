#!/usr/bin/env python3
import os
import sys
import curses

# Path to Angband's monster data file
ANGBAND_MONSTER_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'lib/gamedata/monster.txt')

def parse_monster_file():
    monsters = []
    with open(ANGBAND_MONSTER_FILE, 'r') as file:
        lines = file.readlines()
        current_monster = {}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('name:'):
                if current_monster and 'name' in current_monster:
                    monsters.append(current_monster)
                current_monster = {'name': line[5:].strip()}
            elif line.startswith('hit-points:') and current_monster:
                current_monster['health'] = int(line[11:].strip())
            elif line.startswith('speed:') and current_monster:
                current_monster['speed'] = int(line[6:].strip())
            elif line.startswith('experience:') and current_monster:
                current_monster['experience'] = int(line[11:].strip())
            elif line.startswith('blow:') and current_monster:
                if 'blows' not in current_monster:
                    current_monster['blows'] = []
                current_monster['blows'].append(line[5:].strip())
            elif line.startswith('flags:') and current_monster:
                if 'flags' not in current_monster:
                    current_monster['flags'] = []
                current_monster['flags'].append(line[6:].strip())
            elif line.startswith('flags-off:') and current_monster:
                current_monster['flags_off'] = line[10:].strip()
            elif line.startswith('desc:') and current_monster:
                current_monster['description'] = line[5:].strip()
            elif line.startswith('spell-power:') and current_monster:
                current_monster['spell_power'] = int(line[12:].strip())
            elif line.startswith('rarity:') and current_monster:
                current_monster['rarity'] = int(line[7:].strip())
                
        # Add the last monster
        if current_monster and 'name' in current_monster:
            if 'health' not in current_monster:
                current_monster['health'] = 1
            if 'damage' not in current_monster:
                current_monster['damage'] = 0
            monsters.append(current_monster)
                
    return monsters

def display_monster_list(monsters):
    print("List of Monsters:")
    print("----------------------")
    for i, monster in enumerate(monsters, start=1):
        print(f"{i}. {monster['name']}")
    print("----------------------")
    print("Enter a number to see details (or 'q' to quit): ", end='')

def display_monster_details(monster):
    print("\nMonster Details:")
    print("----------------------")
    print(f"Name: {monster['name']}")
    print(f"Speed: {monster.get('speed', 'Unknown')}")
    print(f"Hit Points: {monster.get('health', 'Unknown')}")
    print(f"Experience: {monster.get('experience', 'Unknown')}")
    
    if 'blows' in monster and monster['blows']:
        print("Blows:")
        for blow in monster['blows']:
            print(f"  - {blow}")
    
    if 'flags' in monster and monster['flags']:
        print("Flags:")
        for flag in monster['flags']:
            print(f"  - {flag}")
    
    if 'flags_off' in monster:
        print(f"Flags Off: {monster['flags_off']}")
    
    if 'description' in monster:
        print(f"Description: {monster['description']}")
    
    if 'spell_power' in monster:
        print(f"Spell Power: {monster['spell_power']}")
    
    if 'rarity' in monster:
        print(f"Rarity: {monster['rarity']}")
    
    print("----------------------")
    input("Press Enter to return to the list...")

def search_monsters(search_term):
    monsters = parse_monster_file()
    results = [monster for monster in monsters if search_term.lower() in monster['name'].lower()]
    if results:
        return results
    else:
        return []

def interactive_mode():
    monsters = parse_monster_file()
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')  # Clear screen
        display_monster_list(monsters)
        choice = input()
        
        if choice.lower() == 'q':
            break
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(monsters):
                os.system('clear' if os.name == 'posix' else 'cls')  # Clear screen
                display_monster_details(monsters[index])
            else:
                input("Invalid selection. Press Enter to continue...")
        except ValueError:
            if choice.lower().startswith('s '):
                search_term = choice[2:]
                results = search_monsters(search_term)
                if results:
                    monsters = results
                else:
                    print(f"No monsters found matching '{search_term}'.")
                    input("Press Enter to continue...")
            else:
                input("Invalid input. Press Enter to continue...")

def safe_addstr(window, y, x, text, attr=0):
    """Safely add a string to a curses window, handling encoding issues."""
    try:
        window.addstr(y, x, text, attr)
    except curses.error as e:
        # Try to add the string without special characters
        try:
            # Replace non-ASCII characters with '?'
            safe_text = ''.join(c if ord(c) < 128 else '?' for c in text)
            window.addstr(y, x, safe_text, attr)
        except curses.error:
            # If still failing, truncate the string to fit
            try:
                height, width = window.getmaxyx()
                if x < width:
                    max_len = width - x - 1
                    truncated = safe_text[:max_len]
                    window.addstr(y, x, truncated, attr)
            except:
                pass  # Give up if all else fails

def init_colors():
    """Initialize color pairs for curses."""
    # Initialize color pairs
    curses.init_pair(1, curses.COLOR_WHITE, -1)  # Default text
    curses.init_pair(2, curses.COLOR_GREEN, -1)  # Headers
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Highlighted items
    curses.init_pair(4, curses.COLOR_RED, -1)  # Important values
    curses.init_pair(5, curses.COLOR_CYAN, -1)  # Secondary information
    
    # Define color constants
    global COLOR_DEFAULT, COLOR_HEADER, COLOR_HIGHLIGHT, COLOR_IMPORTANT, COLOR_INFO
    COLOR_DEFAULT = curses.color_pair(1)
    COLOR_HEADER = curses.color_pair(2) | curses.A_BOLD
    COLOR_HIGHLIGHT = curses.color_pair(3)
    COLOR_IMPORTANT = curses.color_pair(4)
    COLOR_INFO = curses.color_pair(5)

def init_curses():
    """Initialize curses with proper settings."""
    # Start color support
    curses.start_color()
    curses.use_default_colors()
    
    # Initialize colors
    init_colors()
    
    # Hide cursor
    curses.curs_set(0)
    
    # Set up key handling
    curses.meta(1)  # Allow 8-bit input
    curses.raw()    # Disable line buffering
    
    # Define special keys
    curses.keyname(8)  # Ensure backspace is recognized
    curses.keyname(127)  # Ensure delete is recognized
    curses.keyname(curses.KEY_BACKSPACE)  # Ensure KEY_BACKSPACE is recognized

def curses_main(stdscr):
    # Initialize curses with proper settings
    init_curses()
    stdscr.clear()
    stdscr.refresh()  # Initial refresh
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    
    # Create windows
    header_win = curses.newwin(3, width, 0, 0)
    list_win = curses.newwin(height - 6, width, 3, 0)
    status_win = curses.newwin(3, width, height - 3, 0)
    
    # Load monsters
    monsters = parse_monster_file()
    current_monsters = monsters
    
    # Initialize variables
    current_pos = 0
    offset = 0
    search_mode = False
    search_string = ""
    
    # Main loop
    while True:
        # Clear windows
        header_win.clear()
        list_win.clear()
        status_win.clear()
        
        # Draw header
        safe_addstr(header_win, 0, 0, "Angband Monster Editor", COLOR_HEADER)
        safe_addstr(header_win, 1, 0, "=" * (width - 1), COLOR_DEFAULT)
        
        # Draw monster list
        list_height = height - 6
        for i in range(min(list_height, len(current_monsters) - offset)):
            monster = current_monsters[offset + i]
            if offset + i == current_pos:
                safe_addstr(list_win, i, 0, f"> {monster['name']}", curses.A_REVERSE)
            else:
                safe_addstr(list_win, i, 0, f"  {monster['name']}", COLOR_DEFAULT)
        
        # Draw status
        safe_addstr(status_win, 0, 0, "=" * (width - 1), COLOR_DEFAULT)
        if search_mode:
            safe_addstr(status_win, 1, 0, f"Search: {search_string}", COLOR_HIGHLIGHT)
        else:
            safe_addstr(status_win, 1, 0, "q:Quit  s:Search  Enter:View Details  j/k:Navigate", COLOR_INFO)
        
        # Refresh windows
        header_win.refresh()
        list_win.refresh()
        status_win.refresh()
        stdscr.refresh()  # Ensure the main screen is refreshed too
        
        # Get input
        key = stdscr.getch()
        
        if search_mode:
            if key == 27:  # ESC
                search_mode = False
                search_string = ""
            elif key == 10 or key == 13:  # Enter
                search_mode = False
                if search_string:
                    results = search_monsters(search_string)
                    if results:
                        current_monsters = results
                        current_pos = 0
                        offset = 0
                search_string = ""
            elif key == 8 or key == 127 or key == curses.KEY_BACKSPACE:  # Backspace (multiple possible key codes)
                if search_string:
                    search_string = search_string[:-1]
                    # Redraw immediately to show the change
                    status_win.clear()
                    safe_addstr(status_win, 0, 0, "=" * (width - 1), COLOR_DEFAULT)
                    safe_addstr(status_win, 1, 0, f"Search: {search_string}", COLOR_HIGHLIGHT)
                    status_win.refresh()
            elif 32 <= key <= 126:  # Printable characters
                search_string += chr(key)
                # Redraw immediately to show the change
                status_win.clear()
                safe_addstr(status_win, 0, 0, "=" * (width - 1), COLOR_DEFAULT)
                safe_addstr(status_win, 1, 0, f"Search: {search_string}", COLOR_HIGHLIGHT)
                status_win.refresh()
        else:
            if key == ord('q'):
                break
            elif key == ord('s'):
                search_mode = True
                search_string = ""
            elif key == ord('j') or key == curses.KEY_DOWN:
                if current_pos < len(current_monsters) - 1:
                    current_pos += 1
                    if current_pos >= offset + list_height:
                        offset += 1
            elif key == ord('k') or key == curses.KEY_UP:
                if current_pos > 0:
                    current_pos -= 1
                    if current_pos < offset:
                        offset -= 1
            elif key == 10 or key == 13:  # Enter
                if current_monsters:
                    # Show monster details
                    monster = current_monsters[current_pos]
                    detail_win = curses.newwin(height, width, 0, 0)
                    detail_win.clear()
                    
                    # Display monster details
                    safe_addstr(detail_win, 0, 0, f"Monster Details: {monster['name']}", COLOR_HEADER)
                    safe_addstr(detail_win, 1, 0, "=" * (width - 1), COLOR_DEFAULT)
                    
                    line = 3
                    safe_addstr(detail_win, line, 0, "Speed:", COLOR_INFO)
                    safe_addstr(detail_win, line, 7, f"{monster.get('speed', 'Unknown')}", COLOR_DEFAULT)
                    line += 1
                    safe_addstr(detail_win, line, 0, "Hit Points:", COLOR_INFO)
                    safe_addstr(detail_win, line, 12, f"{monster.get('health', 'Unknown')}", COLOR_DEFAULT)
                    line += 1
                    safe_addstr(detail_win, line, 0, "Experience:", COLOR_INFO)
                    safe_addstr(detail_win, line, 12, f"{monster.get('experience', 'Unknown')}", COLOR_DEFAULT)
                    line += 1
                    
                    if 'blows' in monster and monster['blows']:
                        line += 1
                        safe_addstr(detail_win, line, 0, "Blows:", COLOR_INFO)
                        line += 1
                        for blow in monster['blows']:
                            safe_addstr(detail_win, line, 2, f"- {blow}", COLOR_DEFAULT)
                            line += 1
                    
                    if 'flags' in monster and monster['flags']:
                        line += 1
                        safe_addstr(detail_win, line, 0, "Flags:", COLOR_INFO)
                        line += 1
                        for flag in monster['flags']:
                            safe_addstr(detail_win, line, 2, f"- {flag}", COLOR_DEFAULT)
                            line += 1
                    
                    if 'flags_off' in monster:
                        line += 1
                        safe_addstr(detail_win, line, 0, "Flags Off:", COLOR_INFO)
                        safe_addstr(detail_win, line, 11, f"{monster['flags_off']}", COLOR_DEFAULT)
                        line += 1
                    
                    if 'description' in monster:
                        line += 1
                        safe_addstr(detail_win, line, 0, "Description:", COLOR_INFO)
                        safe_addstr(detail_win, line, 13, f"{monster['description']}", COLOR_DEFAULT)
                        line += 1
                    
                    if 'spell_power' in monster:
                        line += 1
                        safe_addstr(detail_win, line, 0, "Spell Power:", COLOR_INFO)
                        safe_addstr(detail_win, line, 13, f"{monster['spell_power']}", COLOR_DEFAULT)
                        line += 1
                    
                    if 'rarity' in monster:
                        line += 1
                        safe_addstr(detail_win, line, 0, "Rarity:", COLOR_INFO)
                        safe_addstr(detail_win, line, 8, f"{monster['rarity']}", COLOR_DEFAULT)
                        line += 1
                    
                    line += 2
                    safe_addstr(detail_win, line, 0, "Press any key to return...", COLOR_HIGHLIGHT)
                    
                    detail_win.refresh()
                    stdscr.refresh()  # Ensure the main screen is refreshed
                    detail_win.getch()

def main():
    # Initialize terminal for better display
    os.environ.setdefault('TERM', 'xterm-256color')
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--search" and len(sys.argv) > 2:
            search_term = sys.argv[2]
            results = search_monsters(search_term)
            if results:
                display_monster_list(results)
                while True:
                    try:
                        choice = input()
                        if choice.lower() == 'q':
                            break
                        index = int(choice) - 1
                        if 0 <= index < len(results):
                            display_monster_details(results[index])
                        else:
                            print("Invalid selection.")
                    except ValueError:
                        print("Invalid input.")
            else:
                print(f"No monsters found matching '{search_term}'.")
        elif sys.argv[1] == "--curses":
            try:
                # Force the terminal to initialize properly
                if os.name == 'posix':
                    os.system('tput init')
                
                # Use wrapper to handle terminal setup/cleanup
                curses.wrapper(curses_main)
            except Exception as e:
                print(f"Error: {type(e).__name__}: {str(e)}")
                print("Falling back to non-curses mode...")
                interactive_mode()
        else:
            print("Usage: show_monsters.py [--search <monster_name>] [--curses]")
    else:
        try:
            # Force the terminal to initialize properly
            if os.name == 'posix':
                os.system('tput init')
                
            # Use wrapper to handle terminal setup/cleanup
            curses.wrapper(curses_main)
        except Exception as e:
            print(f"Error: {type(e).__name__}: {str(e)}")
            print("Falling back to non-curses mode...")
            interactive_mode()

if __name__ == "__main__":
    main()
