import unittest
from Battleship_Game import BoardDisplay, ShipManager, BoardValidator, HumanPlayer, ComputerPlayer, GameSetup, BOARD_SIZE, SHIP_TYPES

class TestBoardDisplay(unittest.TestCase):
    """Test cases for the BoardDisplay class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.display = BoardDisplay()

    def test_color_initialization(self):
        """Test if color codes are correctly initialized"""
        self.assertIn('X', self.display.COLORS)
        self.assertIn('-', self.display.COLORS)
        self.assertIn('RESET', self.display.COLORS)

class TestShipManager(unittest.TestCase):
    """Test cases for the ShipManager class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.ship_manager = ShipManager("Player")

    def test_initialization(self):
        """Test if ship manager is correctly initialized"""
        self.assertEqual(len(self.ship_manager.grid), BOARD_SIZE)
        self.assertEqual(len(self.ship_manager.grid[0]), BOARD_SIZE)
        self.assertEqual(self.ship_manager.ship_locations, {})
        self.assertEqual(self.ship_manager.opponent, "Player")

    def test_ship_deployment(self):
        """Test ship deployment functionality"""
        self.ship_manager.deploy_ship("Destroyer", 2, 0, 0, "H")
        
        # Check if ship is placed correctly
        self.assertEqual(self.ship_manager.grid[0][0], "X")
        self.assertEqual(self.ship_manager.grid[0][1], "X")
        self.assertEqual(len(self.ship_manager.ship_locations["Destroyer"]), 2)

    def test_check_sunk_ship(self):
        """Test ship sinking detection"""
        self.ship_manager.deploy_ship("Destroyer", 2, 0, 0, "H")
        
        # Hit first position
        self.ship_manager.check_sunk_ship(0, 0)
        self.assertIn("Destroyer", self.ship_manager.ship_locations)
        
        # Hit second position
        self.ship_manager.check_sunk_ship(0, 1)
        self.assertNotIn("Destroyer", self.ship_manager.ship_locations)

    def test_all_ships_sunk(self):
        """Test detection of all ships being sunk"""
        self.assertTrue(self.ship_manager.all_ships_sunk())
        
        self.ship_manager.deploy_ship("Destroyer", 2, 0, 0, "H")
        self.assertFalse(self.ship_manager.all_ships_sunk())

class TestBoardValidator(unittest.TestCase):
    """Test cases for the BoardValidator class"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.validator = BoardValidator()
        self.test_grid = [[" "] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    def test_validate_placement(self):
        """Test ship placement validation"""
        # Test valid placements
        self.assertTrue(self.validator.validate_placement(3, 0, 0, "H"))
        self.assertTrue(self.validator.validate_placement(3, 0, 0, "V"))
        
        # Test invalid placements (out of bounds)
        self.assertFalse(self.validator.validate_placement(3, 0, 6, "H"))
        self.assertFalse(self.validator.validate_placement(3, 6, 0, "V"))

    def test_check_overlap(self):
        """Test ship overlap detection"""
        # Place a ship
        self.test_grid[0][0] = "X"
        self.test_grid[0][1] = "X"
        
        # Test overlap detection
        self.assertTrue(self.validator.check_overlap(self.test_grid, 0, 0, "H", 2))
        self.assertFalse(self.validator.check_overlap(self.test_grid, 2, 2, "H", 2))

class TestHumanPlayer(unittest.TestCase):
    """Test cases for the HumanPlayer class"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.player = HumanPlayer()

    def test_initialization(self):
        """Test player initialization"""
        self.assertEqual(self.player.name, "Player")
        self.assertEqual(self.player.opponent_name, "Computer")
        self.assertIsInstance(self.player.ship_manager, ShipManager)
        self.assertIsInstance(self.player.attack_board, ShipManager)
        self.assertIsInstance(self.player.display, BoardDisplay)
        self.assertIsInstance(self.player.validator, BoardValidator)

class TestComputerPlayer(unittest.TestCase):
    """Test cases for the ComputerPlayer class"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.computer = ComputerPlayer()

    def test_initialization(self):
        """Test computer player initialization"""
        self.assertEqual(self.computer.name, "Computer")
        self.assertEqual(self.computer.opponent_name, "Player")
        self.assertIsNone(self.computer.last_hit)
        self.assertEqual(self.computer.hit_stack, [])
        self.assertIsNone(self.computer.direction)

    def test_probability_map_initialization(self):
        """Test probability map initialization"""
        self.computer.update_probability_map(HumanPlayer())
        self.assertEqual(self.computer.probability_map.shape, (BOARD_SIZE, BOARD_SIZE))

class TestGameSetup(unittest.TestCase):
    """Test cases for the GameSetup class"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.setup = GameSetup()

    def test_initialization(self):
        """Test game setup initialization"""
        self.assertEqual(len(self.setup.players), 2)
        self.assertIsInstance(self.setup.players[0], HumanPlayer)
        self.assertIsInstance(self.setup.players[1], ComputerPlayer)

def run_tests():
    """Run all test cases"""
    unittest.main()

if __name__ == '__main__':
    run_tests() 