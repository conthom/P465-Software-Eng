import pytest
import os
import sys
from datetime import datetime

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

# Sample test data
TEST_GAME_DATA = "test_gamedata"
TEST_MONSTER_FILE = os.path.join(TEST_GAME_DATA, "monster.txt")

@pytest.fixture(scope="module", autouse=True)
def setup_test_file():
    """Create a test monster.txt file before tests run, and clean up after."""
    os.makedirs(TEST_GAME_DATA, exist_ok=True)
    with open(TEST_MONSTER_FILE, "w") as f:
        f.write("name:TestMonster\nspeed:100\nhit-points:50\nexperience:200\nblows:2\nflags:UNIQUE,SMART\n")
    yield
    os.remove(TEST_MONSTER_FILE)
    os.rmdir(TEST_GAME_DATA)

def test_monster_edit():
    """Test if the monster's attribute can be updated correctly."""
    monster = Monster({"name": "Test Monster", "speed": "110"})
    monster.update_attribute("speed", "120")
    assert monster.attributes["speed"] == "120"

def test_invalid_attribute_edit():
    """Test updating an invalid attribute."""
    monster = Monster({"name": "Test Monster", "speed": "110"})
    with pytest.raises(KeyError):
        monster.update_attribute("invalid_attr", "100")

def test_file_parsing():
    """Test if the MonsterFileEditor correctly loads monsters from file."""
    mfe = MonsterFileEditor(TEST_GAME_DATA)
    assert len(mfe.monsters) > 0
    assert mfe.monsters[0].attributes["name"] == "TestMonster"

def test_speed_boundary():
    """Test speed boundary values."""
    monster = Monster({"name": "Test Monster", "speed": "10"})
    monster.update_attribute("speed", "1")
    assert monster.attributes["speed"] == "1"  # Lower boundary
    monster.update_attribute("speed", "500")
    assert monster.attributes["speed"] == "500"  # Upper boundary

def test_hit_points_non_negative():
    """Ensure hit points cannot be set to negative values."""
    monster = Monster({"name": "Test Monster", "hit-points": "50"})
    with pytest.raises(ValueError):
        monster.update_attribute("hit-points", "-10")

def test_experience_update():
    """Test updating experience points."""
    monster = Monster({"name": "Test Monster", "experience": "100"})
    monster.update_attribute("experience", "500")
    assert monster.attributes["experience"] == "500"

def test_blows_limited():
    """Ensure the number of blows is within acceptable limits."""
    monster = Monster({"name": "Test Monster", "blows": "2"})
    with pytest.raises(ValueError):
        monster.update_attribute("blows", "5")  # Assuming max is 4

def test_flags_modification():
    """Test adding and removing flags."""
    monster = Monster({"name": "Test Monster", "flags": "UNIQUE,SMART"})
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
    monster = mfe.search_monster("TestMonster")
    assert monster is not None
    assert monster.attributes["name"] == "TestMonster"

def test_search_nonexistent_monster():
    """Test searching for a non-existent monster."""
    mfe = MonsterFileEditor(TEST_GAME_DATA)
    monster = mfe.search_monster("NonExistentMonster")
    assert monster is None

if __name__ == "__main__":
    # Run the tests when the file is executed directly
    pytest.main(["-v", __file__]) 