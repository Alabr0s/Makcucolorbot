"""
Weapon Recall Patterns Module
Contains recoil definitions for Valorant weapons
"""

class Weapon:
    def __init__(self, name, fire_rate, magazine_size, pattern):
        """
        :param name: Weapon name
        :param fire_rate: Rounds per second
        :param magazine_size: Ammo count
        :param pattern: List of (offset_x, offset_y, duration_ms)
        """
        self.name = name
        self.fire_rate = fire_rate
        self.magazine_size = magazine_size
        self.pattern = pattern
        self.time_between_shots = 1000.0 / fire_rate

    @staticmethod
    def get_vandal_pattern():
        """
        Vandal Spray Pattern
        Strong upward recoil, then horizontal sway.
        Updated: Reduced by 30% (User Feedback "Too aggressive").
        """
        pattern = []
        
        # Initial kick (0-9 bullets)
        # Prev Y=11 -> New Y=8
        for _ in range(25): 
            pattern.append((0, 8, 16))

        # TRANSITION PHASE
        # Prev Y=7 -> New Y=5
        for _ in range(10):
            pattern.append((0, 5, 16))
            
        # Sway phase (Left)
        # Prev Y=4 -> New Y=3
        for _ in range(30):
            pattern.append((-3, 3, 16))
            
        # Sway phase (Right)
        for _ in range(30):
            pattern.append((3, 3, 16))
            
        return pattern

    @staticmethod
    def get_phantom_pattern():
        """
        Phantom Spray Pattern
        Updated: Reduced by 30%.
        """
        pattern = []
        
        # Fast upward climb
        # Prev Y=12 -> New Y=9
        for _ in range(20):
            pattern.append((0, 9, 16))

        # TRANSITION PHASE
        # Prev Y=9 -> New Y=6
        for _ in range(10):
            pattern.append((0, 6, 16))
            
        # Stabilize/Sway
        # Prev Y=5 -> New Y=4
        for _ in range(40):
            pattern.append((-2, 4, 16))
            
        for _ in range(40):
            pattern.append((2, 4, 16))
            
        return pattern

    @staticmethod
    def get_spectre_pattern():
        pattern = []
        # Moderate climb
        # Prev Y=10 -> New Y=7
        for _ in range(30):
             pattern.append((0, 7, 16))
        return pattern

class WeaponDatabase:
    def __init__(self):
        self.weapons = {
            "Vandal": Weapon("Vandal", 9.75, 25, Weapon.get_vandal_pattern()),
            "Phantom": Weapon("Phantom", 11.0, 30, Weapon.get_phantom_pattern()),
            "Spectre": Weapon("Spectre", 13.33, 30, Weapon.get_spectre_pattern()),
            "Guardian": Weapon("Guardian", 5.25, 12, [(0, 4, 190)] * 5),
            "No Recoil": Weapon("No Recoil", 1.0, 1, [])
        }
    
    def get_weapon(self, name):
        return self.weapons.get(name)

    def get_all_names(self):
        return list(self.weapons.keys())
