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

def curses_main(stdscr):
    # Initialize curses
    curses.curs_set(0)  # Hide cursor
    stdscr.clear()
    
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
        header_win.addstr(0, 0, "Angband Monster Browser", curses.A_BOLD)
        header_win.addstr(1, 0, "=" * (width - 1))
        
        # Draw monster list
        list_height = height - 6
        for i in range(min(list_height, len(current_monsters) - offset)):
            monster = current_monsters[offset + i]
            if offset + i == current_pos:
                list_win.addstr(i, 0, f"> {monster['name']}", curses.A_REVERSE)
            else:
                list_win.addstr(i, 0, f"  {monster['name']}")
        
        # Draw status
        status_win.addstr(0, 0, "=" * (width - 1))
        if search_mode:
            status_win.addstr(1, 0, f"Search: {search_string}")
        else:
            status_win.addstr(1, 0, "q:Quit  s:Search  Enter:View Details  j/k:Navigate")
        
        # Refresh windows
        header_win.refresh()
        list_win.refresh()
        status_win.refresh()
        
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
            elif key == 8 or key == 127:  # Backspace
                search_string = search_string[:-1]
            elif 32 <= key <= 126:  # Printable characters
                search_string += chr(key)
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
                    detail_win.addstr(0, 0, f"Monster Details: {monster['name']}", curses.A_BOLD)
                    detail_win.addstr(1, 0, "=" * (width - 1))
                    
                    line = 3
                    detail_win.addstr(line, 0, f"Speed: {monster.get('speed', 'Unknown')}")
                    line += 1
                    detail_win.addstr(line, 0, f"Hit Points: {monster.get('health', 'Unknown')}")
                    line += 1
                    detail_win.addstr(line, 0, f"Experience: {monster.get('experience', 'Unknown')}")
                    line += 1
                    
                    if 'blows' in monster and monster['blows']:
                        line += 1
                        detail_win.addstr(line, 0, "Blows:")
                        line += 1
                        for blow in monster['blows']:
                            detail_win.addstr(line, 2, f"- {blow}")
                            line += 1
                    
                    if 'flags' in monster and monster['flags']:
                        line += 1
                        detail_win.addstr(line, 0, "Flags:")
                        line += 1
                        for flag in monster['flags']:
                            detail_win.addstr(line, 2, f"- {flag}")
                            line += 1
                    
                    if 'flags_off' in monster:
                        line += 1
                        detail_win.addstr(line, 0, f"Flags Off: {monster['flags_off']}")
                        line += 1
                    
                    if 'description' in monster:
                        line += 1
                        detail_win.addstr(line, 0, f"Description: {monster['description']}")
                        line += 1
                    
                    if 'spell_power' in monster:
                        line += 1
                        detail_win.addstr(line, 0, f"Spell Power: {monster['spell_power']}")
                        line += 1
                    
                    if 'rarity' in monster:
                        line += 1
                        detail_win.addstr(line, 0, f"Rarity: {monster['rarity']}")
                        line += 1
                    
                    line += 2
                    detail_win.addstr(line, 0, "Press any key to return...")
                    
                    detail_win.refresh()
                    detail_win.getch()

def main():
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
            curses.wrapper(curses_main)
        else:
            print("Usage: show_monsters.py [--search <monster_name>] [--curses]")
    else:
        try:
            curses.wrapper(curses_main)
        except:
            # Fallback to non-curses mode
            interactive_mode()

if __name__ == "__main__":
    main()
