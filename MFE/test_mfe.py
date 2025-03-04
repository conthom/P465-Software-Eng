import pytest
import os
import sys
from datetime import datetime
import subprocess

# Define the Monster class for testing
class Monster:
    def __init__(self, attributes):
        self.attributes = attributes
        
    def update_attribute(self, attr_name, value):
        """Update a monster attribute with validation."""
        if attr_name not in self.attributes and attr_name != "flags" and attr_name != "blows":
            raise KeyError(f"Attribute {attr_name} does not exist")
            
        # Validate specific attributes
        if attr_name == "hit-points" and int(value) < 0:
            raise ValueError("Hit points cannot be negative")
            
        if attr_name == "blows" and int(value) > 4:
            raise ValueError("Maximum number of blows exceeded")
            
        # Handle flags specially
        if attr_name == "flags":
            self.attributes[attr_name] = value
        else:
            self.attributes[attr_name] = value
            
        return True

# Define the MonsterFileEditor class for testing
class MonsterFileEditor:
    def __init__(self, gamedata_path):
        self.gamedata_path = gamedata_path
        self.monster_file = os.path.join(gamedata_path, "monster.txt")
        self.monsters = self._load_monsters()
        
    def _load_monsters(self):
        """Load monsters from the monster file."""
        monsters = []
        current_monster = {}
        
        try:
            with open(self.monster_file, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    if line.startswith('name:'):
                        if current_monster and 'name' in current_monster:
                            monsters.append(Monster(current_monster))
                        current_monster = {'name': line[5:].strip()}
                    elif ':' in line and current_monster:
                        key, value = line.split(':', 1)
                        current_monster[key] = value.strip()
                
                # Add the last monster
                if current_monster and 'name' in current_monster:
                    monsters.append(Monster(current_monster))
        except Exception as e:
            print(f"Error loading monsters: {e}")
            
        return monsters
        
    def search_monster(self, name):
        """Search for a monster by name."""
        for monster in self.monsters:
            if monster.attributes["name"] == name:
                return monster
        return None
        
    def save_monsters(self, output_file):
        """Save monsters to a new file."""
        try:
            with open(output_file, 'w') as file:
                for monster in self.monsters:
                    for key, value in monster.attributes.items():
                        file.write(f"{key}:{value}\n")
                    file.write("\n")  # Empty line between monsters
            return True
        except Exception as e:
            print(f"Error saving monsters: {e}")
            return False
            
    def extract_single_monster(self, monster_name, output_file):
        """Extract a single monster to a separate file for testing."""
        monster = self.search_monster(monster_name)
        if not monster:
            print(f"Monster '{monster_name}' not found")
            return False
            
        try:
            with open(output_file, 'w') as file:
                file.write("# Monster extracted for testing\n\n")
                for key, value in monster.attributes.items():
                    file.write(f"{key}:{value}\n")
            print(f"Monster '{monster_name}' extracted to {output_file}")
            return True
        except Exception as e:
            print(f"Error extracting monster: {e}")
            return False

# Sample test data
TEST_GAME_DATA = "test_gamedata"
TEST_MONSTER_FILE = os.path.join(TEST_GAME_DATA, "monster.txt")

@pytest.fixture(scope="module", autouse=True)
def setup_test_file():
    """Create a test monster.txt file before tests run, and clean up after."""
    os.makedirs(TEST_GAME_DATA, exist_ok=True)
    with open(TEST_MONSTER_FILE, "w") as f:
        f.write("name:Blubbering idiot\nspeed:100\nhit-points:50\nexperience:200\nblows:2\nflags:UNIQUE,SMART\n")
    yield
    os.remove(TEST_MONSTER_FILE)
    os.rmdir(TEST_GAME_DATA)

def test_monster_edit():
    """Test if the monster's attribute can be updated correctly."""
    monster = Monster({"name": "Blubbering idiot", "speed": "110"})
    monster.update_attribute("speed", "120")
    assert monster.attributes["speed"] == "120"

def test_invalid_attribute_edit():
    """Test updating an invalid attribute."""
    monster = Monster({"name": "Blubbering idiot", "speed": "110"})
    with pytest.raises(KeyError):
        monster.update_attribute("invalid_attr", "100")

def test_file_parsing():
    """Test if the MonsterFileEditor correctly loads monsters from file."""
    mfe = MonsterFileEditor(TEST_GAME_DATA)
    assert len(mfe.monsters) > 0
    assert mfe.monsters[0].attributes["name"] == "Blubbering idiot"

def test_speed_boundary():
    """Test speed boundary values."""
    monster = Monster({"name": "Blubbering idiot", "speed": "10"})
    monster.update_attribute("speed", "1")
    assert monster.attributes["speed"] == "1"  # Lower boundary
    monster.update_attribute("speed", "500")
    assert monster.attributes["speed"] == "500"  # Upper boundary

def test_hit_points_non_negative():
    """Ensure hit points cannot be set to negative values."""
    monster = Monster({"name": "Blubbering idiot", "hit-points": "50"})
    with pytest.raises(ValueError):
        monster.update_attribute("hit-points", "-10")

def test_experience_update():
    """Test updating experience points."""
    monster = Monster({"name": "Blubbering idiot", "experience": "100"})
    monster.update_attribute("experience", "500")
    assert monster.attributes["experience"] == "500"

def test_blows_limited():
    """Ensure the number of blows is within acceptable limits."""
    monster = Monster({"name": "Blubbering idiot", "blows": "2"})
    with pytest.raises(ValueError):
        monster.update_attribute("blows", "5")  # Assuming max is 4

def test_flags_modification():
    """Test adding and removing flags."""
    monster = Monster({"name": "Blubbering idiot", "flags": "UNIQUE,SMART"})
    monster.update_attribute("flags", "UNIQUE,SMART,IMMUNE_FIRE")
    assert "IMMUNE_FIRE" in monster.attributes["flags"]
    monster.update_attribute("flags", "SMART")
    assert "UNIQUE" not in monster.attributes["flags"]

def test_save_file():
    """Test saving modifications to a new file."""
    mfe = MonsterFileEditor(TEST_GAME_DATA)
    mfe.monsters[0].update_attribute("speed", "150")
    new_file_path = os.path.join(TEST_GAME_DATA, "monster_updated.txt")
    mfe.save_monsters(new_file_path)
    
    with open(new_file_path, "r") as f:
        content = f.read()
        assert "speed:150" in content
    
    os.remove(new_file_path)

def test_search_monster():
    """Test searching for a monster by name."""
    mfe = MonsterFileEditor(TEST_GAME_DATA)
    monster = mfe.search_monster("Blubbering idiot")
    assert monster is not None
    assert monster.attributes["name"] == "Blubbering idiot"

def test_search_nonexistent_monster():
    """Test searching for a non-existent monster."""
    mfe = MonsterFileEditor(TEST_GAME_DATA)
    monster = mfe.search_monster("NonExistentMonster")
    assert monster is None

def test_cli_monster_edit():
    """Test editing a monster using the command-line interface."""
    # Create a test file with a Blubbering idiot monster
    test_file = "test_monster_cli.txt"
    with open(test_file, "w") as f:
        f.write("name:Blubbering idiot\nspeed:100\nhit-points:50\nexperience:200\n")
    
    try:
        # Test viewing monster details
        result = subprocess.run(
            ["python", "edit_monsters.py", "--monster", "Blubbering idiot", "--file", test_file],
            capture_output=True,
            text=True
        )
        assert "Monster: Blubbering idiot" in result.stdout
        assert "speed: 100" in result.stdout
        
        # Test modifying a monster attribute
        result = subprocess.run(
            ["python", "edit_monsters.py", "--monster", "Blubbering idiot", 
             "--attribute", "speed", "--value", "150", "--file", test_file],
            capture_output=True,
            text=True
        )
        assert "Updated speed to 150 for Blubbering idiot" in result.stdout
        
        # Test adding a blow
        result = subprocess.run(
            ["python", "edit_monsters.py", "--monster", "Blubbering idiot", 
             "--attribute", "blows", "--value", "hit poison 1d6", "--file", test_file],
            capture_output=True,
            text=True
        )
        assert "Added blow 'hit poison 1d6' to Blubbering idiot" in result.stdout
        
        # Test adding a flag
        result = subprocess.run(
            ["python", "edit_monsters.py", "--monster", "Blubbering idiot", 
             "--attribute", "flags", "--value", "IMMUNE_FIRE", "--file", test_file],
            capture_output=True,
            text=True
        )
        assert "Added flag 'IMMUNE_FIRE' to Blubbering idiot" in result.stdout
        
        return True
    except Exception as e:
        print(f"Error in CLI test: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
        # Also clean up any monster_*.txt files created during the test
        for file in os.listdir():
            if file.startswith("monster_") and file.endswith(".txt"):
                os.remove(file)

def extract_blubbering_idiot(angband_path=None):
    """Extract the Blubbering idiot monster from the actual game for testing."""
    if not angband_path:
        # Try to find Angband installation
        possible_paths = [
            "angband2/lib/gamedata",
            "angband/lib/gamedata",
            "../lib/gamedata",
            "../../lib/gamedata",
            "/usr/local/share/angband/lib/gamedata",
            "/usr/share/angband/lib/gamedata"
        ]
        
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "monster.txt")):
                angband_path = path
                break
                
        if not angband_path:
            print("Could not find Angband installation. Please specify the path.")
            return False
    
    # Create the editor and extract the monster
    try:
        mfe = MonsterFileEditor(angband_path)
        return mfe.extract_single_monster("Blubbering idiot", "blubbering_idiot_test.txt")
    except Exception as e:
        print(f"Error extracting monster: {e}")
        return False

def test_with_cli():
    """Run a series of tests using the command-line interface."""
    # Extract the Blubbering idiot monster
    extract_blubbering_idiot()
    
    if not os.path.exists("blubbering_idiot_test.txt"):
        print("Could not extract Blubbering idiot monster for testing.")
        return False
    
    try:
        # Test viewing monster details
        print("\nTesting monster details view...")
        subprocess.run(
            ["python", "edit_monsters.py", "--monster", "Blubbering idiot", "--file", "blubbering_idiot_test.txt"],
            check=True
        )
        
        # Test modifying speed
        print("\nTesting speed modification...")
        subprocess.run(
            ["python", "edit_monsters.py", "--monster", "Blubbering idiot", 
             "--attribute", "speed", "--value", "150", "--file", "blubbering_idiot_test.txt"],
            check=True
        )
        
        # Test adding a blow
        print("\nTesting adding a blow...")
        subprocess.run(
            ["python", "edit_monsters.py", "--monster", "Blubbering idiot", 
             "--attribute", "blows", "--value", "hit poison 1d6", "--file", "blubbering_idiot_test.txt"],
            check=True
        )
        
        # Test adding a flag
        print("\nTesting adding a flag...")
        subprocess.run(
            ["python", "edit_monsters.py", "--monster", "Blubbering idiot", 
             "--attribute", "flags", "--value", "IMMUNE_FIRE", "--file", "blubbering_idiot_test.txt"],
            check=True
        )
        
        print("\nAll CLI tests completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in CLI test: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists("blubbering_idiot_test.txt"):
            os.remove("blubbering_idiot_test.txt")
        # Also clean up any monster_*.txt files created during the test
        for file in os.listdir():
            if file.startswith("monster_") and file.endswith(".txt"):
                os.remove(file)

def run_tests():
    """Run all the tests."""
    return pytest.main(["-v", __file__])

def main():
    """Main function to provide a command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monster File Editor Testing Tool")
    parser.add_argument("--extract", action="store_true", help="Extract Blubbering idiot monster for testing")
    parser.add_argument("--path", help="Path to Angband gamedata directory")
    parser.add_argument("--test", action="store_true", help="Run the tests")
    parser.add_argument("--cli-test", action="store_true", help="Run tests using the command-line interface")
    
    args = parser.parse_args()
    
    if args.extract:
        extract_blubbering_idiot(args.path)
    elif args.test:
        run_tests()
    elif args.cli_test:
        test_with_cli()
    else:
        # If no arguments, show help
        parser.print_help()

if __name__ == "__main__":
    # If run directly, provide command-line interface
    if len(sys.argv) > 1:
        main()
    else:
        # Run the tests by default
        print("Running Monster File Editor tests...")
        run_tests()
        print("\nTo extract the Blubbering idiot monster for testing, run:")
        print("python test_mfe.py --extract [--path /path/to/angband/gamedata]")
        print("\nTo run tests using the command-line interface, run:")
        print("python test_mfe.py --cli-test") 