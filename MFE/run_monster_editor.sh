#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the Angband root directory
cd "$SCRIPT_DIR"

# Run the monster editor with proper paths
python3 src/MFE/edit_monsters.py

# Exit with the same status as the Python script
exit $?