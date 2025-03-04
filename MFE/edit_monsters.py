import os
import sys
import curses
from datetime import datetime
import argparse
import shutil

# Path to Angband's monster data file
ANGBAND_MONSTER_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'lib/gamedata/monster.txt')

# Add these constants after the ANGBAND_MONSTER_FILE definition
BLOW_EFFECTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'lib/gamedata/blow_effects.txt')
BLOW_METHODS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'lib/gamedata/blow_methods.txt')

# Track modified monsters
modified_monsters = set()

def get_yes_no(window, prompt, highlight_color):
    """Handle yes/no confirmation prompts."""
    window.erase()
    window.addstr(0, 0, prompt, highlight_color)
    window.refresh()
    while True:
        key = window.getch()
        if key in (ord('y'), ord('Y')):
            return True
        if key in (ord('n'), ord('N'), 27):  # 27 is ESC
            return False

def navigate_list(current_pos, key, items, offset=None, list_height=None):
    """Handle list navigation with optional scrolling."""
    new_pos = current_pos
    new_offset = offset

    if key == ord('j') and current_pos < len(items) - 1:
        new_pos += 1
        if offset is not None and list_height and new_pos >= offset + list_height:
            new_offset = offset + 1
    elif key == ord('k') and current_pos > 0:
        new_pos -= 1
        if offset is not None and new_pos < offset:
            new_offset = offset - 1

    return new_pos, new_offset

def handle_menu_input(key, valid_keys):
    """Handle menu key input with validation."""
    if chr(key).lower() in valid_keys:
        return chr(key).lower()
    return None

def handle_input_editing(status_win, width, initial_value="", prompt=""):
    """Common function to handle input editing with proper cursor movement."""
    # Save the current content of the status window to restore it later
    status_content = []
    for y in range(3):  # Status window is typically 3 lines
        try:
            line = status_win.instr(y, 0, width - 1).decode('utf-8')
            status_content.append(line)
        except:
            status_content.append("")
    
    # Now handle the editing
    status_win.erase()
    status_win.addstr(0, 0, prompt, COLOR_HIGHLIGHT)
    status_win.addstr(1, 0, " " * (width - 1))  # Clear input line
    status_win.move(1, 0)
    status_win.refresh()
    
    curses.echo()
    curses.curs_set(1)  # Show cursor
    
    edit_buffer = list(initial_value)
    input_pos = len(edit_buffer)
    
    while True:
        status_win.addstr(1, 0, " " * (width - 1))  # Clear line
        status_win.addstr(1, 0, ''.join(edit_buffer))
        status_win.move(1, input_pos)
        status_win.refresh()
        
        ch = status_win.getch()
        
        if ch == 27:  # ESC
            result = None
            break
        elif ch == 10 or ch == 13:  # Enter
            result = ''.join(edit_buffer)
            break
        elif ch in (curses.KEY_BACKSPACE, 8, 127):  # Backspace
            if input_pos > 0:
                edit_buffer.pop(input_pos - 1)
                input_pos -= 1
        elif ch == curses.KEY_DC:  # Delete
            if input_pos < len(edit_buffer):
                edit_buffer.pop(input_pos)
        elif 32 <= ch <= 126:  # Printable characters
            if input_pos < len(edit_buffer):
                edit_buffer.insert(input_pos, chr(ch))
            else:
                edit_buffer.append(chr(ch))
            input_pos += 1
    
    curses.noecho()
    curses.curs_set(0)  # Hide cursor
    
    # Restore the status window content
    status_win.erase()
    for y, line in enumerate(status_content):
        if line:
            status_win.addstr(y, 0, line)
    status_win.refresh()
    
    return result

def parse_monster_file():
    monsters = []
    with open(ANGBAND_MONSTER_FILE, 'r') as file:
        lines = file.readlines()[240:]
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

def search_monsters(search_term):
    monsters = parse_monster_file()
    results = [monster for monster in monsters if search_term.lower() in monster['name'].lower()]
    if results:
        return results
    else:
        return []

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

def get_status_text(line):
    """Generate appropriate status text based on the selected line."""
    field_info = get_field_info(line)
    if field_info:
        field_name, field_type = field_info
        return f"e:Edit {field_name}    q:Exit  j:Down  k:Up"
    else:
        return "q:Exit  j:Down  k:Up"

def get_field_info(line):
    """Extract field information from a content line."""
    if len(line) == 4:  # Label and value with different attributes
        label, _, value, _ = line
        
        # Extract field name from label (remove colon)
        field_name = label.strip().lower().replace(':', '')
        
        # Determine field type based on field name and value
        if field_name in ['speed', 'hit points', 'experience', 'spell power', 'rarity']:
            return field_name, 'int'
        elif field_name in ['description', 'flags off']:
            return field_name, 'str'
    elif len(line) == 2:  # For blows and flags sections
        text, _ = line
        text = text.strip()
        if text == "Blows:":
            return 'blows', 'str'
        elif text == "Flags:":
            return 'flags', 'str'
    
    return None

def show_monster_details(win, monster, height, width):
    """Display monster details in a scrollable window."""
    # Create a status window at the bottom
    detail_win = curses.newwin(height - 3, width, 0, 0)  # Main content window
    status_win = curses.newwin(3, width, height - 3, 0)  # Status window
    
    # Make a copy of the monster data so we can edit it without affecting the original
    monster_copy = monster.copy()
    
    # Dictionary mapping display field names to monster dict keys
    field_to_key = {
        'speed': 'speed',
        'hit points': 'health',
        'experience': 'experience',
        'spell power': 'spell_power',
        'rarity': 'rarity',
        'description': 'description',
        'flags off': 'flags_off',
        'flags': 'flags',
        'blows': 'blows'
    }
    
    # Prepare all the content lines first
    content_lines = generate_monster_content(monster_copy, width)
    
    # Initialize scrolling variables
    scroll_pos = 0
    max_scroll = max(0, len(content_lines) - (height - 5))  # -5 for borders and status
    
    # Initialize selection variable
    selected_line = 3  # Start with speed selected
    
    # Track if changes were made
    changes_made = False
    
    # Main loop for scrollable view
    while True:
        detail_win.clear()
        status_win.clear()
        
        # Display visible content
        for i in range(min(height - 4, len(content_lines) - scroll_pos)):
            line_idx = scroll_pos + i
            line = content_lines[line_idx]
            
            if line_idx == selected_line:
                attr_modifier = curses.A_REVERSE
            else:
                attr_modifier = 0
                
            if len(line) == 2:
                text, attr = line
                safe_addstr(detail_win, i, 0, text, attr | attr_modifier)
            elif len(line) == 4:
                label, label_attr, value, value_attr = line
                safe_addstr(detail_win, i, 0, label, label_attr | attr_modifier)
                safe_addstr(detail_win, i, len(label) + 1, value, value_attr | attr_modifier)
        
        # Draw status window
        safe_addstr(status_win, 0, 0, "=" * (width - 1), COLOR_DEFAULT)
        status_text = get_status_text(content_lines[selected_line] if selected_line < len(content_lines) else None)
        safe_addstr(status_win, 1, 0, status_text, COLOR_INFO)
        
        # Refresh windows
        detail_win.refresh()
        status_win.refresh()
        
        # Get input
        key = detail_win.getch()
        
        if key == ord('q') or key == 27:  # q or ESC to quit
            if changes_made:
                # Update the original monster and mark as modified
                for key, value in monster_copy.items():
                    monster[key] = value
                modified_monsters.add(monster['name'])
            break
        elif key == ord('s'):  # Save changes
            if changes_made:
                if save_monster_changes(monster, monster_copy):
                    safe_addstr(status_win, 2, 0, "Changes saved successfully!", COLOR_HIGHLIGHT)
                    status_win.refresh()
                    detail_win.getch()  # Wait for keypress
                else:
                    safe_addstr(status_win, 2, 0, "Error saving changes.", COLOR_IMPORTANT)
                    status_win.refresh()
                    detail_win.getch()  # Wait for keypress
                changes_made = False
            else:
                safe_addstr(status_win, 2, 0, "No changes to save.", COLOR_INFO)
                status_win.refresh()
                detail_win.getch()  # Wait for keypress
        # Handle navigation
        elif key in (ord('j'), ord('k')):
            new_line = selected_line
            if key == ord('j'):  # Move down
                next_line = selected_line + 1
                while next_line < len(content_lines):
                    line = content_lines[next_line]
                    if len(line) == 4 or (len(line) == 2 and line[0].strip() and not line[0].startswith('=')):
                        new_line = next_line
                        break
                    next_line += 1
            else:  # Move up
                prev_line = selected_line - 1
                while prev_line >= 0:
                    line = content_lines[prev_line]
                    if len(line) == 4 or (len(line) == 2 and line[0].strip() and not line[0].startswith('=')):
                        new_line = prev_line
                        break
                    prev_line -= 1
                    
            if new_line != selected_line:
                selected_line = new_line
                # Adjust scroll position if needed
                if selected_line >= scroll_pos + height - 4:
                    scroll_pos = min(max_scroll, selected_line - height + 5)
                elif selected_line < scroll_pos:
                    scroll_pos = max(0, selected_line)
        elif key == ord('e'):  # e to edit selected field
            field_info = get_field_info(content_lines[selected_line] if selected_line < len(content_lines) else None)
            if field_info:
                field_name, field_type = field_info
                if field_name == 'blows':
                    # Create a new window for the blow editor
                    edit_win = curses.newwin(height, width, 0, 0)
                    if edit_monster_blow(edit_win, monster_copy, height, width):
                        changes_made = True
                        # Regenerate content lines with updated data
                        content_lines = generate_monster_content(monster_copy, width)
                    # Clean up the window
                    del edit_win
                    # Redraw the main windows
                    detail_win.clear()
                    status_win.clear()
                    detail_win.refresh()
                    status_win.refresh()
                elif field_name == 'flags':
                    # Create a new window for the flag editor
                    edit_win = curses.newwin(height, width, 0, 0)
                    if edit_monster_flags(edit_win, monster_copy, height, width):
                        changes_made = True
                        # Regenerate content lines with updated data
                        content_lines = generate_monster_content(monster_copy, width)
                    # Clean up the window
                    del edit_win
                    # Redraw the main windows
                    detail_win.clear()
                    status_win.clear()
                    detail_win.refresh()
                    status_win.refresh()
                else:
                    # Handle other field editing...
                    field_key = field_to_key.get(field_name)
                    if not field_key:
                        continue
                    
                    edited_value = handle_input_editing(
                        status_win,
                        width,
                        initial_value=str(monster_copy.get(field_key, '')),
                        prompt=f"Edit {field_name} (Enter to confirm, ESC to cancel):"
                    )
                    
                    if edited_value is not None:
                        try:
                            if field_type == "int":
                                value = int(edited_value)
                                monster_copy[field_key] = value
                                changes_made = True
                            else:
                                monster_copy[field_key] = edited_value
                                changes_made = True
                            
                            content_lines = generate_monster_content(monster_copy, width)
                        except ValueError:
                            safe_addstr(status_win, 2, 0, f"Invalid input - expected {field_type}", COLOR_IMPORTANT)
                            status_win.refresh()
                            detail_win.getch()

def generate_monster_content(monster, width):
    """Generate content lines for monster details display."""
    content_lines = []
    
    # Add header
    content_lines.append((f"Monster Details: {monster['name']}", COLOR_HEADER))
    content_lines.append(("=" * (width - 1), COLOR_DEFAULT))
    content_lines.append(("", COLOR_DEFAULT))  # Empty line
    
    # Basic stats
    content_lines.append(("Speed:", COLOR_INFO, f"{monster.get('speed', 'None')}", COLOR_DEFAULT))
    content_lines.append(("Hit Points:", COLOR_INFO, f"{monster.get('health', 'None')}", COLOR_DEFAULT))
    content_lines.append(("Experience:", COLOR_INFO, f"{monster.get('experience', 'None')}", COLOR_DEFAULT))
    content_lines.append(("", COLOR_DEFAULT))  # Empty line
    
    # Blows
    content_lines.append(("Blows:", COLOR_INFO))
    if 'blows' in monster and monster['blows']:
        for blow in monster['blows']:
            content_lines.append(("  - " + blow, COLOR_DEFAULT))
    else:
        content_lines.append(("  None", COLOR_DEFAULT))
    content_lines.append(("", COLOR_DEFAULT))  # Empty line
    
    # Flags
    content_lines.append(("Flags:", COLOR_INFO))
    if 'flags' in monster and monster['flags']:
        for flag in monster['flags']:
            content_lines.append(("  - " + flag, COLOR_DEFAULT))
    else:
        content_lines.append(("  None", COLOR_DEFAULT))
    content_lines.append(("", COLOR_DEFAULT))  # Empty line
    
    # Flags Off
    content_lines.append(("Flags Off:", COLOR_INFO, 
                         f"{monster.get('flags_off', 'None')}", COLOR_DEFAULT))
    content_lines.append(("", COLOR_DEFAULT))  # Empty line
    
    # Description
    content_lines.append(("Description:", COLOR_INFO, 
                         f"{monster.get('description', 'None')}", COLOR_DEFAULT))
    content_lines.append(("", COLOR_DEFAULT))  # Empty line
    
    # Spell Power
    content_lines.append(("Spell Power:", COLOR_INFO, 
                         f"{monster.get('spell_power', 'None')}", COLOR_DEFAULT))
    
    # Rarity
    content_lines.append(("Rarity:", COLOR_INFO, 
                         f"{monster.get('rarity', 'None')}", COLOR_DEFAULT))
    
    return content_lines

def save_all_changes(monsters):
    """Save all changes to the original monster file and create a backup."""
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"monster_{timestamp}.txt"
    backup_filepath = os.path.join(os.path.dirname(ANGBAND_MONSTER_FILE), backup_filename)
    
    try:
        # Create backup of original file
        shutil.copy2(ANGBAND_MONSTER_FILE, backup_filepath)
        
        # Read the original file to preserve comments and structure
        with open(ANGBAND_MONSTER_FILE, 'r') as file:
            lines = file.readlines()
        
        # Create a map of monster names to their data
        monster_map = {m['name']: m for m in monsters}
        
        # Process the file line by line
        new_lines = []
        current_monster = None
        skip_until_next = False
        
        for line in lines:
            if line.startswith('name:'):
                monster_name = line[5:].strip()
                if monster_name in modified_monsters:
                    # This is a modified monster - skip original entries
                    skip_until_next = True
                    current_monster = monster_map[monster_name]
                    # Write the updated monster data
                    new_lines.append(f"name:{current_monster['name']}\n")
                    if 'speed' in current_monster:
                        new_lines.append(f"speed:{current_monster['speed']}\n")
                    if 'health' in current_monster:
                        new_lines.append(f"hit-points:{current_monster['health']}\n")
                    if 'experience' in current_monster:
                        new_lines.append(f"experience:{current_monster['experience']}\n")
                    if 'blows' in current_monster:
                        for blow in current_monster['blows']:
                            # Ensure blow is properly formatted as "blow:METHOD:EFFECT:DAMAGE"
                            if ':' in blow:
                                # If already in format METHOD:EFFECT:DAMAGE, just add "blow:" prefix
                                new_lines.append(f"blow:{blow}\n")
                            else:
                                # If in space-separated format, convert to proper format
                                parts = blow.split()
                                if len(parts) >= 3:
                                    method = parts[0].upper()
                                    effect = parts[1].upper()
                                    damage = parts[2]
                                    new_lines.append(f"blow:{method}:{effect}:{damage}\n")
                                else:
                                    # If can't parse properly, just save as-is with "blow:" prefix
                                    new_lines.append(f"blow:{blow}\n")
                    if 'flags' in current_monster:
                        for flag in current_monster['flags']:
                            new_lines.append(f"flags:{flag}\n")
                    if 'flags_off' in current_monster:
                        new_lines.append(f"flags-off:{current_monster['flags_off']}\n")
                    if 'description' in current_monster:
                        new_lines.append(f"desc:{current_monster['description']}\n")
                    if 'spell_power' in current_monster:
                        new_lines.append(f"spell-power:{current_monster['spell_power']}\n")
                    if 'rarity' in current_monster:
                        new_lines.append(f"rarity:{current_monster['rarity']}\n")
                else:
                    skip_until_next = False
                    new_lines.append(line)
            elif not skip_until_next:
                new_lines.append(line)
            elif line.strip() == "":
                skip_until_next = False
                new_lines.append(line)
        
        # Write changes directly to the original file
        with open(ANGBAND_MONSTER_FILE, 'w') as file:
            file.writelines(new_lines)
        
        return backup_filepath, ANGBAND_MONSTER_FILE
    except Exception as e:
        print(f"Error saving changes: {e}")
        return None, None

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
                if modified_monsters:
                    # Ask user if they want to save changes
                    status_win.clear()
                    safe_addstr(status_win, 0, 0, "Save changes before exit? (y/n)", COLOR_HIGHLIGHT)
                    status_win.refresh()
                    
                    save_choice = stdscr.getch()
                    if save_choice == ord('y'):
                        new_file = save_all_changes(monsters)
                        if new_file:
                            status_win.clear()
                            safe_addstr(status_win, 0, 0, f"Changes saved to: {os.path.basename(new_file)}", COLOR_INFO)
                            status_win.refresh()
                            stdscr.getch()  # Wait for key press
                break
            elif key == ord('s'):
                search_mode = True
                search_string = ""
            # Handle navigation
            elif key in (ord('j'), ord('k')):
                new_pos, new_offset = navigate_list(current_pos, key, current_monsters, offset, list_height)
                if new_pos != current_pos or new_offset != offset:
                    current_pos = new_pos
                    offset = new_offset
            elif key == 10 or key == 13:  # Enter
                if current_monsters:
                    # Show monster details
                    monster = current_monsters[current_pos]
                    detail_win = curses.newwin(height, width, 0, 0)
                    
                    # Create a scrollable details view
                    show_monster_details(detail_win, monster, height, width)

def parse_blow_data(filename):
    """Parse blow effects or methods file."""
    data = {}
    with open(filename, 'r') as file:
        current_name = None
        current_desc = []
        
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('name:'):
                if current_name:
                    data[current_name] = '\n'.join(current_desc)
                current_name = line[5:].strip()
                current_desc = []
            elif line.startswith('desc:'):
                current_desc.append(line[5:].strip())
                
        if current_name:
            data[current_name] = '\n'.join(current_desc)
            
    return data

def edit_monster_blow(window, monster, height, width):
    """Edit a monster's blow attacks with a simplified interface that works on smaller screens."""
    # Use a single window approach instead of multiple windows
    window.clear()
    window.refresh()
    
    # Load blow effects and methods
    try:
        effects = parse_blow_data(BLOW_EFFECTS_FILE)
        methods = parse_blow_data(BLOW_METHODS_FILE)
    except Exception as e:
        window.addstr(0, 0, f"Error loading blow data: {str(e)}")
        window.refresh()
        window.getch()
        return False
    
    # Get current blows
    blows = monster.get('blows', [])
    if not blows:
        blows = []
    
    current_pos = 0
    changes_made = False
    
    # Calculate available space
    list_height = height - 6  # Reserve space for header and footer
    
    while True:
        window.clear()
        
        # Draw header
        window.addstr(0, 0, "Blow Editor", COLOR_HEADER)
        window.addstr(1, 0, "=" * (width - 1), COLOR_DEFAULT)
        
        # Show current blows
        window.addstr(2, 0, "Current Blows:", COLOR_INFO)
        
        # Calculate visible range based on current position
        visible_start = max(0, current_pos - (list_height // 2))
        visible_end = min(len(blows), visible_start + list_height)
        
        if blows:
            for i in range(visible_start, visible_end):
                y_pos = 3 + (i - visible_start)
                if i == current_pos:
                    window.addstr(y_pos, 0, f"> {blows[i]}", curses.A_REVERSE)
                else:
                    window.addstr(y_pos, 0, f"  {blows[i]}", COLOR_DEFAULT)
        else:
            window.addstr(3, 2, "No blows defined", COLOR_DEFAULT)
        
        # Draw footer with commands
        footer_y = height - 3
        window.addstr(footer_y, 0, "=" * (width - 1), COLOR_DEFAULT)
        window.addstr(footer_y + 1, 0, "a:Add  e:Edit  d:Delete  j/k:Navigate  q/ESC:Back", COLOR_INFO)
        
        # Refresh window
        window.refresh()
        
        # Get input
        try:
            key = window.getch()
        except:
            break
            
        if key in (ord('q'), 27):  # q or ESC to quit
            if changes_made:
                monster['blows'] = blows
            break
            
        # Handle navigation
        if key == ord('j') and current_pos < len(blows) - 1:
            current_pos += 1
        elif key == ord('k') and current_pos > 0:
            current_pos -= 1
            
        # Handle menu actions
        if key == ord('a'):  # Add new blow
            prompt = "Enter new blow (method effect damage) or ESC to cancel:"
            window.addstr(footer_y + 1, 0, prompt, COLOR_HIGHLIGHT)
            window.clrtoeol()
            window.refresh()
            
            curses.echo()
            curses.curs_set(1)  # Show cursor
            
            try:
                new_blow = ""
                input_pos = len(prompt) + 1  # Position after the prompt
                window.move(footer_y + 1, input_pos)
                
                # Get input character by character
                ch = window.getch()
                while ch != 27 and ch != 10 and ch != 13:  # Not ESC and not Enter
                    if ch in (curses.KEY_BACKSPACE, 8, 127):  # Backspace
                        if new_blow:
                            new_blow = new_blow[:-1]
                            # Clear the line after the prompt
                            window.addstr(footer_y + 1, input_pos, " " * (width - input_pos))
                            # Redraw the input
                            window.addstr(footer_y + 1, input_pos, new_blow)
                            window.move(footer_y + 1, input_pos + len(new_blow))
                    elif 32 <= ch <= 126:  # Printable characters
                        new_blow += chr(ch)
                        window.addstr(footer_y + 1, input_pos + len(new_blow) - 1, chr(ch))
                    window.refresh()
                    ch = window.getch()
                
                if ch == 27:  # ESC pressed
                    new_blow = None
                
            except:
                new_blow = None
            finally:
                curses.noecho()
                curses.curs_set(0)  # Hide cursor
            
            if new_blow:
                parts = new_blow.split()
                if len(parts) >= 3:  # Need at least method, effect, and damage
                    method = parts[0].upper()  # Convert to uppercase
                    effect = parts[1].upper()  # Convert to uppercase
                    damage = parts[2]
                    
                    # Check if method and effect exist (case-insensitive)
                    method_exists = method in methods or method.lower() in [m.lower() for m in methods]
                    effect_exists = effect in effects or effect.lower() in [e.lower() for e in effects]
                    
                    if method_exists and effect_exists:
                        # Format the blow properly: METHOD:EFFECT:DAMAGE
                        formatted_blow = f"{method}:{effect}:{damage}"
                        blows.append(formatted_blow)
                        current_pos = len(blows) - 1
                        changes_made = True
                    else:
                        window.addstr(footer_y + 1, 0, "Unknown method or effect", COLOR_IMPORTANT)
                        window.clrtoeol()
                        window.refresh()
                        window.getch()
                else:
                    window.addstr(footer_y + 1, 0, "Invalid format. Use: method effect damage", COLOR_IMPORTANT)
                    window.clrtoeol()
                    window.refresh()
                    window.getch()
                
        elif key == ord('e') and blows:  # Edit blow
            if current_pos < len(blows):
                # Parse the current blow to display in a more user-friendly format
                current_blow = blows[current_pos]
                parts = current_blow.split(':')
                if len(parts) >= 3:
                    display_blow = f"{parts[0]} {parts[1]} {parts[2]}"
                else:
                    display_blow = current_blow
                
                prompt = "Edit blow (method effect damage) or ESC to cancel:"
                window.addstr(footer_y + 1, 0, prompt, COLOR_HIGHLIGHT)
                window.clrtoeol()
                window.refresh()
                
                curses.echo()
                curses.curs_set(1)  # Show cursor
                
                try:
                    # Initialize edit buffer with current value
                    edited_blow = display_blow
                    input_pos = len(prompt) + 1  # Position after the prompt
                    
                    # Show initial value
                    window.addstr(footer_y + 1, input_pos, edited_blow)
                    window.move(footer_y + 1, input_pos + len(edited_blow))
                    
                    # Get input character by character
                    ch = window.getch()
                    while ch != 27 and ch != 10 and ch != 13:  # Not ESC and not Enter
                        if ch in (curses.KEY_BACKSPACE, 8, 127):  # Backspace
                            if edited_blow:
                                edited_blow = edited_blow[:-1]
                                # Clear the line after the prompt
                                window.addstr(footer_y + 1, input_pos, " " * (width - input_pos))
                                # Redraw the input
                                window.addstr(footer_y + 1, input_pos, edited_blow)
                                window.move(footer_y + 1, input_pos + len(edited_blow))
                        elif 32 <= ch <= 126:  # Printable characters
                            edited_blow += chr(ch)
                            window.addstr(footer_y + 1, input_pos + len(edited_blow) - 1, chr(ch))
                        window.refresh()
                        ch = window.getch()
                    
                    if ch == 27:  # ESC pressed
                        edited_blow = None
                        
                except:
                    edited_blow = None
                finally:
                    curses.noecho()
                    curses.curs_set(0)  # Hide cursor
                
                if edited_blow:
                    parts = edited_blow.split()
                    if len(parts) >= 3:  # Need at least method, effect, and damage
                        method = parts[0].upper()  # Convert to uppercase
                        effect = parts[1].upper()  # Convert to uppercase
                        damage = parts[2]
                        
                        # Check if method and effect exist (case-insensitive)
                        method_exists = method in methods or method.lower() in [m.lower() for m in methods]
                        effect_exists = effect in effects or effect.lower() in [e.lower() for e in effects]
                        
                        if method_exists and effect_exists:
                            # Format the blow properly: METHOD:EFFECT:DAMAGE
                            formatted_blow = f"{method}:{effect}:{damage}"
                            blows[current_pos] = formatted_blow
                            changes_made = True
                        else:
                            window.addstr(footer_y + 1, 0, "Unknown method or effect", COLOR_IMPORTANT)
                            window.clrtoeol()
                            window.refresh()
                            window.getch()
                    else:
                        window.addstr(footer_y + 1, 0, "Invalid format. Use: method effect damage", COLOR_IMPORTANT)
                        window.clrtoeol()
                        window.refresh()
                        window.getch()
                
        elif key == ord('d') and blows:  # Delete blow
            if current_pos < len(blows):
                window.addstr(footer_y + 1, 0, "Delete this blow? (y/n)", COLOR_HIGHLIGHT)
                window.clrtoeol()
                window.refresh()
                
                confirm = window.getch()
                if confirm in (ord('y'), ord('Y')):
                    del blows[current_pos]
                    if current_pos >= len(blows):
                        current_pos = max(0, len(blows) - 1)
                    changes_made = True
    
    return changes_made

def edit_monster_flags(window, monster, height, width):
    """Edit a monster's flags with a simplified interface that works on smaller screens."""
    # Use a single window approach instead of multiple windows
    window.clear()
    window.refresh()
    
    # Get current flags
    flags = monster.get('flags', [])
    if not flags:
        flags = []
    
    current_pos = 0
    changes_made = False
    
    # Calculate available space
    list_height = height - 6  # Reserve space for header and footer
    
    while True:
        window.clear()
        
        # Draw header
        window.addstr(0, 0, "Flag Editor", COLOR_HEADER)
        window.addstr(1, 0, "=" * (width - 1), COLOR_DEFAULT)
        
        # Show current flags
        window.addstr(2, 0, "Current Flags:", COLOR_INFO)
        
        # Calculate visible range based on current position
        visible_start = max(0, current_pos - (list_height // 2))
        visible_end = min(len(flags), visible_start + list_height)
        
        if flags:
            for i in range(visible_start, visible_end):
                y_pos = 3 + (i - visible_start)
                if i == current_pos:
                    window.addstr(y_pos, 0, f"> {flags[i]}", curses.A_REVERSE)
                else:
                    window.addstr(y_pos, 0, f"  {flags[i]}", COLOR_DEFAULT)
        else:
            window.addstr(3, 2, "No flags defined", COLOR_DEFAULT)
        
        # Draw footer with commands
        footer_y = height - 3
        window.addstr(footer_y, 0, "=" * (width - 1), COLOR_DEFAULT)
        window.addstr(footer_y + 1, 0, "a:Add  e:Edit  d:Delete  j/k:Navigate  q/ESC:Back", COLOR_INFO)
        
        # Refresh window
        window.refresh()
        
        # Get input
        try:
            key = window.getch()
        except:
            break
            
        if key in (ord('q'), 27):  # q or ESC to quit
            if changes_made:
                monster['flags'] = flags
            break
            
        # Handle navigation
        if key == ord('j') and current_pos < len(flags) - 1:
            current_pos += 1
        elif key == ord('k') and current_pos > 0:
            current_pos -= 1
            
        # Handle Enter key for editing
        if key in (10, 13):  # Enter
            if not flags:  # Add new flag if list is empty
                key = ord('a')
            else:  # Edit existing flag
                key = ord('e')
            
        # Handle menu actions
        if key == ord('a'):  # Add new flag
            prompt = "Enter new flag or ESC to cancel:"
            window.addstr(footer_y + 1, 0, prompt, COLOR_HIGHLIGHT)
            window.clrtoeol()
            window.refresh()
            
            curses.echo()
            curses.curs_set(1)  # Show cursor
            
            try:
                new_flag = ""
                input_pos = len(prompt) + 1  # Position after the prompt
                window.move(footer_y + 1, input_pos)
                
                # Get input character by character
                ch = window.getch()
                while ch != 27 and ch != 10 and ch != 13:  # Not ESC and not Enter
                    if ch in (curses.KEY_BACKSPACE, 8, 127):  # Backspace
                        if new_flag:
                            new_flag = new_flag[:-1]
                            # Clear the line after the prompt
                            window.addstr(footer_y + 1, input_pos, " " * (width - input_pos))
                            # Redraw the input
                            window.addstr(footer_y + 1, input_pos, new_flag)
                            window.move(footer_y + 1, input_pos + len(new_flag))
                    elif 32 <= ch <= 126:  # Printable characters
                        new_flag += chr(ch)
                        window.addstr(footer_y + 1, input_pos + len(new_flag) - 1, chr(ch))
                    window.refresh()
                    ch = window.getch()
                
                if ch == 27:  # ESC pressed
                    new_flag = None
                    
            except:
                new_flag = None
            finally:
                curses.noecho()
                curses.curs_set(0)  # Hide cursor
            
            if new_flag:
                # Convert flag to uppercase for consistency
                parts = new_flag.split()
                if len(parts) > 0:
                    # If the flag has multiple parts (like "SMART OPEN"), convert each part
                    formatted_flag = ' '.join([part.upper() for part in parts])
                    flags.append(formatted_flag)
                    current_pos = len(flags) - 1
                    changes_made = True
                
        elif key == ord('e') and flags:  # Edit flag
            if current_pos < len(flags):
                prompt = "Edit flag or ESC to cancel:"
                window.addstr(footer_y + 1, 0, prompt, COLOR_HIGHLIGHT)
                window.clrtoeol()
                window.refresh()
                
                curses.echo()
                curses.curs_set(1)  # Show cursor
                
                try:
                    # Initialize edit buffer with current value
                    current_flag = flags[current_pos]
                    edited_flag = current_flag
                    input_pos = len(prompt) + 1  # Position after the prompt
                    
                    # Show initial value
                    window.addstr(footer_y + 1, input_pos, edited_flag)
                    window.move(footer_y + 1, input_pos + len(edited_flag))
                    
                    # Get input character by character
                    ch = window.getch()
                    while ch != 27 and ch != 10 and ch != 13:  # Not ESC and not Enter
                        if ch in (curses.KEY_BACKSPACE, 8, 127):  # Backspace
                            if edited_flag:
                                edited_flag = edited_flag[:-1]
                                # Clear the line after the prompt
                                window.addstr(footer_y + 1, input_pos, " " * (width - input_pos))
                                # Redraw the input
                                window.addstr(footer_y + 1, input_pos, edited_flag)
                                window.move(footer_y + 1, input_pos + len(edited_flag))
                        elif 32 <= ch <= 126:  # Printable characters
                            edited_flag += chr(ch)
                            window.addstr(footer_y + 1, input_pos + len(edited_flag) - 1, chr(ch))
                        window.refresh()
                        ch = window.getch()
                    
                    if ch == 27:  # ESC pressed
                        edited_flag = None
                        
                except:
                    edited_flag = None
                finally:
                    curses.noecho()
                    curses.curs_set(0)  # Hide cursor
                
                if edited_flag:
                    # Convert flag to uppercase for consistency
                    parts = edited_flag.split()
                    if len(parts) > 0:
                        # If the flag has multiple parts (like "SMART OPEN"), convert each part
                        formatted_flag = ' '.join([part.upper() for part in parts])
                        flags[current_pos] = formatted_flag
                        changes_made = True
                    
        elif key == ord('d') and flags:  # Delete flag
            if current_pos < len(flags):
                window.addstr(footer_y + 1, 0, "Delete this flag? (y/n)", COLOR_HIGHLIGHT)
                window.clrtoeol()
                window.refresh()
                
                confirm = window.getch()
                if confirm in (ord('y'), ord('Y')):
                    del flags[current_pos]
                    if current_pos >= len(flags):
                        current_pos = max(0, len(flags) - 1)
                    changes_made = True
    
    return changes_made

def main():
    # Initialize terminal for better display
    os.environ.setdefault('TERM', 'xterm-256color')
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Angband Monster Editor")
    parser.add_argument("--test", action="store_true", help="Run test mode: modify Blubbering idiot and save")
    args = parser.parse_args()
    
    try:
        if args.test:
            # Load monsters
            monsters = parse_monster_file()
            # Find Blubbering idiot
            blubbering_idiot = None
            for monster in monsters:
                if monster['name'].lower() == "blubbering idiot":
                    blubbering_idiot = monster
                    break
            
            if blubbering_idiot:
                # Make some test modifications
                blubbering_idiot['speed'] = 140
                blubbering_idiot['health'] = 200
                blubbering_idiot['blows'] = ["CLAW:HURT:15d6", "BITE:POISON:2d6"]
                blubbering_idiot['flags'] = ["UNIQUE", "SMART", "EVIL"]
                modified_monsters.add(blubbering_idiot['name'])
                
                # Save changes
                backup_file, game_file = save_all_changes(monsters)
                if backup_file and game_file:
                    print(f"\nTest changes made successfully!")
                    print(f"Backup saved to: {os.path.basename(backup_file)}")
                    print(f"Changes written to: {os.path.basename(game_file)}")
                    print("\nChanges made to Blubbering idiot:")
                    print("- Speed: 140")
                    print("- Hit Points: 200")
                    print("- Blows: CLAW:HURT:15d6, BITE:POISON:2d6")
                    print("- Flags: UNIQUE, SMART, EVIL")
                    print("\nTo use these changes:")
                    print("1. The game file has been automatically updated")
                    print("2. Run 'make' to rebuild the game")
                    print("3. Run './angband' to play with the changes")
                else:
                    print("Error: Failed to save changes")
            else:
                print("Error: Could not find Blubbering idiot monster")
        else:
            # Force the terminal to initialize properly
            if os.name == 'posix':
                os.system('tput init')
                
            # Use wrapper to handle terminal setup/cleanup
            curses.wrapper(curses_main)
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()