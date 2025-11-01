import unittest
from main import GameState, GameEngine, Upgrade


class TestIsUpgradeUnlocked(unittest.TestCase):
    """Test suite for the is_upgrade_unlocked method."""
    
    def setUp(self):
        """Set up the game engine for each test."""
        self.engine = GameEngine()
        
    def test_upgrade_unlocked_all_requirements_met(self):
        """Test that is_upgrade_unlocked returns True when all requirements are met and upgrade is not purchased."""
        # Create a state with 5 cursors (enough for 'reinforced_index_finger' which requires 1 cursor)
        state = GameState(
            cookies=0,
            cookies_baked=0,
            buildings={'cursor': 5},
            cps=0,
            time_ms=0,
            last_click_time_ms=-20,
            last_production_frame=-1,
            click_power=1,
            upgrades=set()  # Upgrade not purchased
        )
        
        # 'reinforced_index_finger' requires 1 cursor
        result = self.engine.is_upgrade_unlocked('reinforced_index_finger', state)
        self.assertTrue(result, "Upgrade should be unlocked when building requirement is met and not purchased")
        
    def test_upgrade_unlocked_false_when_already_purchased(self):
        """Test that is_upgrade_unlocked returns False when upgrade is already purchased."""
        # Create a state with enough cursors and the upgrade already purchased
        state = GameState(
            cookies=0,
            cookies_baked=0,
            buildings={'cursor': 5},
            cps=0,
            time_ms=0,
            last_click_time_ms=-20,
            last_production_frame=-1,
            click_power=1,
            upgrades={'reinforced_index_finger'}  # Upgrade already purchased
        )
        
        result = self.engine.is_upgrade_unlocked('reinforced_index_finger', state)
        self.assertFalse(result, "Upgrade should not be unlocked if already purchased")
        
    def test_upgrade_unlocked_false_when_building_requirements_not_met(self):
        """Test that is_upgrade_unlocked returns False when building requirements are not met."""
        # Create a state without enough cursors
        state = GameState(
            cookies=0,
            cookies_baked=0,
            buildings={'cursor': 0},  # 0 cursors, need at least 1
            cps=0,
            time_ms=0,
            last_click_time_ms=-20,
            last_production_frame=-1,
            click_power=1,
            upgrades=set()
        )
        
        # 'reinforced_index_finger' requires 1 cursor
        result = self.engine.is_upgrade_unlocked('reinforced_index_finger', state)
        self.assertFalse(result, "Upgrade should not be unlocked when building requirement is not met")
        
    def test_upgrade_handles_no_building_requirements(self):
        """Test that is_upgrade_unlocked correctly handles upgrades with no building requirements."""
        # Cookie upgrades typically have no building requirements (building_tie=None, unlock_requirement=0)
        state = GameState(
            cookies=0,
            cookies_baked=0,
            buildings={},  # No buildings at all
            cps=0,
            time_ms=0,
            last_click_time_ms=-20,
            last_production_frame=-1,
            click_power=1,
            upgrades=set()
        )
        
        # 'plain_cookies' is a cookie upgrade with no building requirement
        result = self.engine.is_upgrade_unlocked('plain_cookies', state)
        self.assertTrue(result, "Upgrade with no building requirements should be unlocked by default")
        
    def test_upgrade_checks_multiple_building_requirements(self):
        """Test that is_upgrade_unlocked correctly checks multiple building requirements."""
        # Test with an upgrade that requires multiple buildings of the same type
        # 'carpal_tunnel_prevention_cream' requires 5 cursors
        
        # Case 1: Exactly the required amount
        state_exact = GameState(
            cookies=0,
            cookies_baked=0,
            buildings={'cursor': 5},  # Exactly 5 cursors
            cps=0,
            time_ms=0,
            last_click_time_ms=-20,
            last_production_frame=-1,
            click_power=1,
            upgrades=set()
        )
        result_exact = self.engine.is_upgrade_unlocked('carpal_tunnel_prevention_cream', state_exact)
        self.assertTrue(result_exact, "Upgrade should be unlocked when exactly meeting the requirement")
        
        # Case 2: More than required
        state_more = GameState(
            cookies=0,
            cookies_baked=0,
            buildings={'cursor': 10},  # More than 5 cursors
            cps=0,
            time_ms=0,
            last_click_time_ms=-20,
            last_production_frame=-1,
            click_power=1,
            upgrades=set()
        )
        result_more = self.engine.is_upgrade_unlocked('carpal_tunnel_prevention_cream', state_more)
        self.assertTrue(result_more, "Upgrade should be unlocked when exceeding the requirement")
        
        # Case 3: Less than required
        state_less = GameState(
            cookies=0,
            cookies_baked=0,
            buildings={'cursor': 4},  # Only 4 cursors, need 5
            cps=0,
            time_ms=0,
            last_click_time_ms=-20,
            last_production_frame=-1,
            click_power=1,
            upgrades=set()
        )
        result_less = self.engine.is_upgrade_unlocked('carpal_tunnel_prevention_cream', state_less)
        self.assertFalse(result_less, "Upgrade should not be unlocked when below the requirement")
        
        # Case 4: Building doesn't exist in state (should treat as 0)
        state_missing = GameState(
            cookies=0,
            cookies_baked=0,
            buildings={},  # No buildings
            cps=0,
            time_ms=0,
            last_click_time_ms=-20,
            last_production_frame=-1,
            click_power=1,
            upgrades=set()
        )
        result_missing = self.engine.is_upgrade_unlocked('carpal_tunnel_prevention_cream', state_missing)
        self.assertFalse(result_missing, "Upgrade should not be unlocked when building type is missing from state")


if __name__ == '__main__':
    unittest.main()
