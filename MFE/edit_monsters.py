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
    curses.keyname(curses.KEY_LEFT)  # Ensure left arrow is recognized
    curses.keyname(curses.KEY_RIGHT)  # Ensure right arrow is recognized

def get_status_text(line):
    """Generate appropriate status text based on the selected line."""
    field_info = get_field_info(line)
    if field_info:
        field_name, field_type = field_info
        return f"e:Edit {field_name}  s:Save  q:Exit  j:Down  k:Up"
    else:
        return "s:Save  q:Exit  j:Down  k:Up"

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
        'flags off': 'flags_off'
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
        for i in range(min(height - 4, len(content_lines) - scroll_pos)):  # -4 to leave room for borders and status
            line_idx = scroll_pos + i
            line = content_lines[line_idx]
            
            # Highlight the selected line
            if line_idx == selected_line:
                attr_modifier = curses.A_REVERSE
            else:
                attr_modifier = 0
                
            if len(line) == 2:  # Just text and attribute
                text, attr = line
                safe_addstr(detail_win, i, 0, text, attr | attr_modifier)
            elif len(line) == 4:  # Label and value with different attributes
                label, label_attr, value, value_attr = line
                safe_addstr(detail_win, i, 0, label, label_attr | attr_modifier)
                safe_addstr(detail_win, i, len(label) + 1, value, value_attr | attr_modifier)
        
        # Draw status window border and content
        safe_addstr(status_win, 0, 0, "=" * (width - 1), COLOR_DEFAULT)
        
        # Get and display status text
        status_text = get_status_text(content_lines[selected_line] if selected_line < len(content_lines) else None)
        safe_addstr(status_win, 1, 0, status_text, COLOR_INFO)
        
        # Refresh windows
        detail_win.refresh()
        status_win.refresh()
        
        # Get input
        key = detail_win.getch()
        
        if key == ord('s'):  # Save changes
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
        elif key == ord('q') or key == 27:  # q or ESC to quit
            if changes_made:
                # Ask if user wants to save before exiting
                safe_addstr(status_win, 2, 0, "Save changes before exit? (y/n)", COLOR_HIGHLIGHT)
                status_win.refresh()
                choice = detail_win.getch()
                if choice == ord('y'):
                    save_monster_changes(monster, monster_copy)
            break
        elif key == ord('j'):  # j to move down
            # Find next non-empty line
            if selected_line < len(content_lines) - 1:
                next_line = selected_line + 1
                # Skip empty lines
                while next_line < len(content_lines) - 1:
                    line = content_lines[next_line]
                    # Check if this is an empty line (contains only an empty string)
                    if len(line) == 2 and line[0] == "":
                        next_line += 1
                    else:
                        break
                        
                selected_line = next_line
                # Adjust scroll position if needed
                if selected_line >= scroll_pos + height - 4:
                    scroll_pos = min(max_scroll, selected_line - height + 5)
        elif key == ord('k'):  # k to move up
            # Find previous non-empty line
            if selected_line > 3:  # Don't go above line 3 (after the header)
                prev_line = selected_line - 1
                # Skip empty lines
                while prev_line > 3:  # Don't go above line 3
                    line = content_lines[prev_line]
                    # Check if this is an empty line (contains only an empty string)
                    if len(line) == 2 and line[0] == "":
                        prev_line -= 1
                    else:
                        break
                        
                selected_line = prev_line
                # Adjust scroll position if needed
                if selected_line < scroll_pos:
                    scroll_pos = max(0, selected_line)
        elif key == ord('e'):  # e to edit selected field
            field_info = get_field_info(content_lines[selected_line] if selected_line < len(content_lines) else None)
            
            if field_info:
                field_name, field_type = field_info
                # Map display field name to monster dictionary key
                field_key = field_to_key.get(field_name)
                
                if not field_key:
                    continue  # Skip if we don't know how to handle this field
                
                # Show edit prompt
                status_win.clear()
                safe_addstr(status_win, 0, 0, "=" * (width - 1), COLOR_DEFAULT)
                safe_addstr(status_win, 1, 0, f"Edit {field_name} (Enter to confirm, ESC to cancel):", COLOR_HIGHLIGHT)
                
                # Get current value
                current_value = str(monster_copy.get(field_key, ''))
                
                # Edit field
                curses.echo()  # Show typed characters
                curses.curs_set(1)  # Show cursor
                
                # Clear input area
                status_win.addstr(2, 0, " " * (width - 1))
                status_win.refresh()
                
                # Get input
                input_value = ""
                input_pos = 0
                edit_buffer = []
                
                while True:
                    # Display current input
                    status_win.addstr(2, 0, " " * (width - 1))  # Clear line
                    status_win.addstr(2, 0, ''.join(edit_buffer))
                    status_win.move(2, input_pos)  # Position cursor
                    status_win.refresh()
                    
                    ch = status_win.getch()
                    
                    if ch == 10 or ch == 13:  # Enter
                        input_value = ''.join(edit_buffer)
                        break
                    elif ch == 27:  # ESC
                        input_value = None
                        break
                    elif ch == curses.KEY_BACKSPACE or ch == 8 or ch == 127:  # Backspace
                        if input_pos > 0:
                            edit_buffer.pop(input_pos - 1)
                            input_pos -= 1
                    elif 32 <= ch <= 126:  # Printable characters
                        if input_pos < len(edit_buffer):
                            edit_buffer.insert(input_pos, chr(ch))
                        else:
                            edit_buffer.append(chr(ch))
                        input_pos += 1
                    elif ch == curses.KEY_LEFT and input_pos > 0:
                        input_pos -= 1
                    elif ch == curses.KEY_RIGHT and input_pos < len(edit_buffer):
                        input_pos += 1
                
                curses.noecho()  # Stop showing typed characters
                curses.curs_set(0)  # Hide cursor
                
                # Process input
                if input_value is not None:
                    # Validate input based on field type
                    valid_input = True
                    try:
                        if field_type == "int":
                            # Validate integer input
                            value = int(input_value)
                            monster_copy[field_key] = value
                        else:  # Default to string
                            monster_copy[field_key] = input_value
                        
                        # Mark changes as made
                        changes_made = True
                        
                        # Regenerate content lines with updated data
                        content_lines = generate_monster_content(monster_copy, width)
                        
                    except ValueError:
                        valid_input = False
                        safe_addstr(status_win, 2, 0, f"Invalid input - expected {field_type}", COLOR_IMPORTANT)
                        status_win.refresh()
                        detail_win.getch()  # Wait for keypress
                else:
                    # User cancelled
                    safe_addstr(status_win, 2, 0, "Edit cancelled", COLOR_INFO)
                    status_win.refresh()
                    detail_win.getch()  # Wait for keypress

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

def save_monster_changes(original_monster, edited_monster):
    """Save changes made to a monster back to the data file."""
    try:
        # Read the entire file
        with open(ANGBAND_MONSTER_FILE, 'r') as file:
            lines = file.readlines()
        
        # Find the monster in the file
        monster_name = original_monster['name']
        in_target_monster = False
        monster_start_idx = -1
        monster_end_idx = -1
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('name:') and line[5:].strip() == monster_name:
                in_target_monster = True
                monster_start_idx = i
            elif in_target_monster and (line.startswith('name:') or i == len(lines) - 1):
                monster_end_idx = i - 1 if line.startswith('name:') else i
                break
        
        if monster_start_idx == -1:
            return False  # Monster not found
        
        # Create updated lines for the monster
        updated_lines = []
        
        # Add the name line
        updated_lines.append(f"name:{edited_monster['name']}\n")
        
        # Add other attributes
        if 'speed' in edited_monster:
            updated_lines.append(f"speed:{edited_monster['speed']}\n")
            
        if 'health' in edited_monster:
            updated_lines.append(f"hit-points:{edited_monster['health']}\n")
            
        if 'experience' in edited_monster:
            updated_lines.append(f"experience:{edited_monster['experience']}\n")
        
        # Add blows
        if 'blows' in edited_monster and edited_monster['blows']:
            for blow in edited_monster['blows']:
                updated_lines.append(f"blow:{blow}\n")
        
        # Add flags
        if 'flags' in edited_monster and edited_monster['flags']:
            for flag in edited_monster['flags']:
                updated_lines.append(f"flags:{flag}\n")
        
        # Add other fields
        if 'flags_off' in edited_monster:
            updated_lines.append(f"flags-off:{edited_monster['flags_off']}\n")
            
        if 'description' in edited_monster:
            updated_lines.append(f"desc:{edited_monster['description']}\n")
            
        if 'spell_power' in edited_monster:
            updated_lines.append(f"spell-power:{edited_monster['spell_power']}\n")
            
        if 'rarity' in edited_monster:
            updated_lines.append(f"rarity:{edited_monster['rarity']}\n")
        
        # Merge the updated lines with the file
        new_lines = lines[:monster_start_idx] + updated_lines + lines[monster_end_idx+1:]
        
        # Write the file back
        with open(ANGBAND_MONSTER_FILE, 'w') as file:
            file.writelines(new_lines)
        
        # Update the original monster with the edited values
        for key, value in edited_monster.items():
            original_monster[key] = value
            
        return True
    except Exception as e:
        print(f"Error saving changes: {e}")
        return False

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
            elif key == ord('j'):
                if current_pos < len(current_monsters) - 1:
                    current_pos += 1
                    if current_pos >= offset + list_height:
                        offset += 1
            elif key == ord('k'):
                if current_pos > 0:
                    current_pos -= 1
                    if current_pos < offset:
                        offset -= 1
            elif key == 10 or key == 13:  # Enter
                if current_monsters:
                    # Show monster details
                    monster = current_monsters[current_pos]
                    detail_win = curses.newwin(height, width, 0, 0)
                    
                    # Create a scrollable details view
                    show_monster_details(detail_win, monster, height, width)

def main():
    # Initialize terminal for better display
    os.environ.setdefault('TERM', 'xterm-256color')
    
    try:
            # Force the terminal to initialize properly
            if os.name == 'posix':
                os.system('tput init')
                
            # Use wrapper to handle terminal setup/cleanup
            curses.wrapper(curses_main)
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()
