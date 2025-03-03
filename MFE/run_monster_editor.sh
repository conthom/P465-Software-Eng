#!/bin/bash

echo "Setting permissions for run_monster_editor.sh..."
sudo chmod +x run_monster_editor.sh
echo "Permissions set successfully."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the Angband root directory
cd "$SCRIPT_DIR"

# Run the monster editor with proper paths
python3 src/MFE/edit_monsters.py

# Exit with the same status as the Python script
exit $?