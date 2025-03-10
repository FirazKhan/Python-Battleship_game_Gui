import random
import numpy as np
import json

# Load configuration from JSON file
with open('config.json', 'r') as f:
    config = json.load(f)

# Use configuration values
SHIP_TYPES = config['ships']
LETTERS_TO_NUMS = config['grid_letters']
BOARD_SIZE = config['board_size']

class BoardDisplay:
    """Handles the visual representation of the game board with colored output"""
    def __init__(self):
        # Define color codes for different board elements
        self.COLORS = {
            'X': '\033[92m',  # Green for ships/hits
            '-': '\033[91m',  # Red for misses
            'RESET': '\033[0m'  # Reset color formatting
        }

    def display_board(self, grid):
        print("  A B C D E F G H")
        print("  +-+-+-+-+-+-+-+")
        row_num = 1
        for row in grid:
            formatted_row = []
            for cell in row:
                if cell in self.COLORS:
                    formatted_row.append(f"{self.COLORS[cell]}{cell}{self.COLORS['RESET']}")
                else:
                    formatted_row.append(cell)
            print("%d|%s|" % (row_num, "|".join(formatted_row)))
            row_num += 1

class ShipManager:
    """Manages the game board state and ship placements"""
    def __init__(self, opponent):
        # Initialize empty grid and ship tracking
        self.grid = [[" "] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.ship_locations = {}  # Dictionary to track ship positions
        self.opponent = opponent

    def deploy_ship(self, ship, length, row, column, orientation):
        """Places a ship on the board and records its location"""
        if orientation == "H":  # Horizontal placement
            for i in range(column, column + length):
                self.grid[row][i] = "X"
                self.ship_locations.setdefault(ship, []).append((row, i))
        else:  # Vertical placement
            for i in range(row, row + length):
                self.grid[i][column] = "X"
                self.ship_locations.setdefault(ship, []).append((i, column))

    def check_sunk_ship(self, row, column):
        for ship, positions in self.ship_locations.items():
            if (row, column) in positions:
                positions.remove((row, column))
                if not positions:
                    print("\n*******************************************")
                    print(f"\033[1m        {self.opponent} has sunk the {ship}!\033[0m")
                    print("*******************************************\n")
                    del self.ship_locations[ship]
                    break

    def all_ships_sunk(self):
        return all(not positions for positions in self.ship_locations.values())

class BoardValidator:
    """Validates ship placements and board positions"""
    def __init__(self):
        self.size = BOARD_SIZE

    def validate_placement(self, length, row, column, orientation):
        """Checks if a ship placement is within board boundaries"""
        if orientation == "H":
            return column + length <= self.size
        else:
            return row + length <= self.size

    def check_overlap(self, grid, row, column, orientation, length):
        """Checks if a ship placement overlaps with existing ships"""
        try:
            if orientation == "H":
                return any(grid[row][i] == "X" for i in range(column, column + length))
            else:
                return any(grid[i][column] == "X" for i in range(row, row + length))
        except IndexError:
            return True
        return False

class BasePlayer:
    """Base class for player functionality"""
    def __init__(self, name):
        # Initialize player components and attributes
        self.name = name
        self.opponent_name = "Computer" if name == "Player" else "Player"
        self.ship_manager = ShipManager(self.opponent_name)  # Manages player's ships
        self.attack_board = ShipManager(self.opponent_name)  # Tracks attacks made
        self.display = BoardDisplay()  # Handles board display
        self.validator = BoardValidator()  # Validates moves
        self.hit_directions = [(0,1), (0,-1), (1,0), (-1,0)]  # Possible attack directions

    def can_place_ship(self, opponent, row, col, length, orientation):
        if orientation == "H":
            if col + length > BOARD_SIZE:
                return False
            for i in range(length):
                if self.attack_board.grid[row][col + i] in ["-", "X"]:
                    return False
        else:
            if row + length > BOARD_SIZE:
                return False
            for i in range(length):
                if self.attack_board.grid[row + i][col] in ["-", "X"]:
                    return False
        return True

class HumanPlayer(BasePlayer):
    def __init__(self):
        super().__init__("Player")

    def take_turn(self, opponent):
        while True:
            try:
                position = input("Enter the position (e.g., A2): ").upper()
                if len(position) < 2 or position[0] not in 'ABCDEFGH' or not position[1:].isdigit():
                    raise ValueError("Invalid position. Please enter a valid position (e.g., A2).\n")
                column = LETTERS_TO_NUMS[position[0]]
                row = int(position[1:]) - 1
                if row < 0 or row >= BOARD_SIZE or column < 0 or column >= BOARD_SIZE:
                    raise ValueError("Position out of bounds. Please enter a valid position within the grid.\n")
                break
            except ValueError as e:
                print(e)
            
        if self.attack_board.grid[row][column] in ["-", "X"]:
            print("\nYou already attacked this position. Try again.\n")
            return self.take_turn(opponent)
        elif opponent.ship_manager.grid[row][column] == "X":
            self.attack_board.grid[row][column] = "X"
            print("\nHit!\n")
            print('\033[1m       Player`s Guess Board\033[0m')
            self.display.display_board(self.attack_board.grid)
            opponent.ship_manager.check_sunk_ship(row, column)
        else:
            self.attack_board.grid[row][column] = "-"
            print("\nMiss!\n")
            print('\033[1m       Player`s Guess Board\033[0m')
            self.display.display_board(self.attack_board.grid)

class ComputerPlayer(BasePlayer):
    """AI player with intelligent targeting system"""
    def __init__(self):
        super().__init__("Computer")
        # Initialize AI targeting attributes
        self.last_hit = None  # Stores last successful hit
        self.hit_stack = []  # Queue of potential target positions
        self.direction = None  # Current targeting direction (H or V)
        self.probability_map = np.zeros((BOARD_SIZE, BOARD_SIZE))  # Heat map for targeting

    def take_turn(self, opponent):
        # Initial setup - create probability map if it doesn't exist
        if not hasattr(self, 'probability_map'):
            self.probability_map = np.zeros((BOARD_SIZE, BOARD_SIZE))

        row = None
        column = None

        # First Priority - Check hit stack for potential targets
        if self.hit_stack:
            row, column = self.hit_stack.pop(0)
        # Second Priority - Use last hit information
        elif self.last_hit:
            row, column = self.last_hit
            if self.direction:
                # If we know the ship's direction, try moves along that line
                if self.direction == "H":
                    possible_moves = [(row, column-1), (row, column+1)]
                else:
                    possible_moves = [(row-1, column), (row+1, column)]
                
                # Filter out invalid or already tried moves
                possible_moves = [(r, c) for r, c in possible_moves 
                                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE 
                                and self.attack_board.grid[r][c] not in ["-", "X"]]
                
                if possible_moves:
                    row, column = random.choice(possible_moves)
                else:
                    # Reset targeting if no valid moves in current direction
                    self.last_hit = None
                    self.direction = None
                    self.hit_stack = []
                    self.update_probability_map(opponent)
                    row, column = np.unravel_index(np.argmax(self.probability_map), self.probability_map.shape)
            else:
                # Try all adjacent positions if direction unknown
                possible_moves = [(row-1, column), (row+1, column), (row, column-1), (row, column+1)]
                possible_moves = [(r, c) for r, c in possible_moves 
                                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE 
                                and self.attack_board.grid[r][c] not in ["-", "X"]]
                if possible_moves:
                    row, column = random.choice(possible_moves)
                else:
                    # Reset targeting if no valid adjacent moves
                    self.last_hit = None
                    self.direction = None
                    self.hit_stack = []
                    self.update_probability_map(opponent)
                    row, column = np.unravel_index(np.argmax(self.probability_map), self.probability_map.shape)
        # Third Priority - Use probability map for targeting
        else:
            self.update_probability_map(opponent)
            row, column = np.unravel_index(np.argmax(self.probability_map), self.probability_map.shape)

        # Process the attack result
        if opponent.ship_manager.grid[row][column] == "X":
            # Handle successful hit
            self.attack_board.grid[row][column] = "X"
            print("\nComputer hit!\n")
            
            if self.last_hit:
                # Determine ship orientation based on multiple hits
                if row == self.last_hit[0]:
                    self.direction = "H"
                elif column == self.last_hit[1]:
                    self.direction = "V"
                
                # Add next potential moves based on ship direction
                if self.direction == "H":
                    next_moves = [(row, min(column, self.last_hit[1])-1), 
                                (row, max(column, self.last_hit[1])+1)]
                else:  # Vertical
                    next_moves = [(min(row, self.last_hit[0])-1, column), 
                                (max(row, self.last_hit[0])+1, column)]
                
                # Filter valid moves and add to hit stack
                valid_moves = [(r, c) for r, c in next_moves 
                              if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE 
                              and self.attack_board.grid[r][c] not in ["-", "X"]]
                self.hit_stack.extend(valid_moves)
            
            self.last_hit = (row, column)
            print('\033[1m       Computer`s Guess Board\033[0m')
            self.display.display_board(self.attack_board.grid)
            opponent.ship_manager.check_sunk_ship(row, column)
        else:
            # Handle miss
            self.attack_board.grid[row][column] = "-"
            print("\nComputer miss!\n")
            print('\033[1m       Computer`s Guess Board\033[0m')
            self.display.display_board(self.attack_board.grid)

    def update_probability_map(self, opponent):
        """Updates probability map for intelligent targeting"""
        # Reset the probability map
        self.probability_map.fill(0)
        
        # First mark all attacked positions with zero probability
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.attack_board.grid[row][col] in ["-", "X"]:
                    self.probability_map[row][col] = 0
                    continue
            
                # Initialize non-attacked positions with base probability
                self.probability_map[row][col] = 1
        
        # Calculate additional probabilities for possible ship placements
        for ship, length in SHIP_TYPES.items():
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    # Check horizontal placement possibility
                    if self.can_place_ship(opponent, row, col, length, "H"):
                        for i in range(length):
                            # Only increment if position hasn't been attacked
                            if self.attack_board.grid[row][col + i] not in ["-", "X"]:
                                self.probability_map[row][col + i] += 1
                    # Check vertical placement possibility
                    if self.can_place_ship(opponent, row, col, length, "V"):
                        for i in range(length):
                            # Only increment if position hasn't been attacked
                            if self.attack_board.grid[row + i][col] not in ["-", "X"]:
                                self.probability_map[row + i][col] += 1

    def get_move(self, opponent):
        if self.last_hit:
            row, col = self.last_hit
            random.shuffle(self.hit_directions)
            
            for dr, dc in self.hit_directions:
                new_row = row + dr
                new_col = col + dc
                
                if (0 <= new_row < BOARD_SIZE and 
                    0 <= new_col < BOARD_SIZE and 
                    opponent.ship_manager.grid[new_row][new_col] not in ["-", "H"]):
                    return new_row, new_col
            
            self.last_hit = None

        while True:
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - 1)
            
            if opponent.ship_manager.grid[row][col] not in ["-", "H"]:
                if opponent.ship_manager.grid[row][col] == "X":
                    self.last_hit = (row, col)
                return row, col

class GameSetup:
    """Handles game initialization and ship placement"""
    def __init__(self):
        self.players = [HumanPlayer(), ComputerPlayer()]

    def deploy_all_ships(self, player):
        """Manages the ship deployment phase for each player"""
        if player.name == "Player":
            print("\n\033[1m       Place Your Ships\033[0m")
            print("----------------------------------------\n")

        for ship, length in SHIP_TYPES.items():
            if player.name == "Player":
                print(f"Place the {ship} (length: {length})")
                print("----------------------------------------")
            
            while True:
                if player.name == "Computer":
                    orientation = random.choice(["H", "V"])
                    row = random.randint(0, BOARD_SIZE - 1)
                    column = random.randint(0, BOARD_SIZE - 1)
                else:
                    row, column, orientation = self.get_user_input(True, length, player)
                if player.validator.validate_placement(length, row, column, orientation):
                    if not player.validator.check_overlap(player.ship_manager.grid, row, column, orientation, length):
                        player.ship_manager.deploy_ship(ship, length, row, column, orientation)
                        if player.name != "Computer":
                            player.display.display_board(player.ship_manager.grid)
                            print("----------------------------------------\n")
                        break
        if player.name == "Computer":
            print('===============================================')

    def get_user_input(self, place_ship, ship_length=None, player=None):
        if place_ship:
            while True:
                try:
                    orientation = input("Enter orientation Horizontal - H or Vertical - V: ").upper()
                    if orientation not in ["H", "V"]:
                        raise ValueError("Invalid orientation. Please enter 'H' for Horizontal or 'V' for Vertical.\n")
                    break
                except ValueError as e:
                    print(e)
            while True:
                try:
                    position = input("Enter the position (e.g., A2): ").upper()
                    if len(position) < 2 or position[0] not in 'ABCDEFGH' or not position[1:].isdigit():
                        raise ValueError("Invalid position. Please enter a valid position (e.g., A2).\n")
                    column = LETTERS_TO_NUMS[position[0]]
                    row = int(position[1:]) - 1
                    if row < 0 or row >= BOARD_SIZE or column < 0 or column >= BOARD_SIZE:
                        raise ValueError("Position out of bounds. Please enter a valid position within the grid.\n")
                    if ship_length and not player.validator.validate_placement(ship_length, row, column, orientation):
                        raise ValueError("The ship cannot be placed at this position due to size constraints.\n")
                    if player and player.validator.check_overlap(player.ship_manager.grid, row, column, orientation, ship_length):
                        raise ValueError("A ship is already placed at this position. Please enter another location.\n")
                    break
                except ValueError as e:
                    print(e)
            return row, column, orientation
        else:
            while True:
                try:
                    position = input("Enter the position (e.g., A2): ").upper()
                    if len(position) < 2 or position[0] not in 'ABCDEFGH' or not position[1:].isdigit():
                        raise ValueError("Invalid position. Please enter a valid position (e.g., A2).\n")
                    column = LETTERS_TO_NUMS[position[0]]
                    row = int(position[1:]) - 1
                    if row < 0 or row >= BOARD_SIZE or column < 0 or column >= BOARD_SIZE:
                        raise ValueError("Position out of bounds. Please enter a valid position within the grid.\n")
                    break
                except ValueError as e:
                    print(e)
            return row, column

class GameLoop:
    """Manages the main game loop and turn sequence"""
    def __init__(self, players):
        self.players = players
        self.current_player = 0

    def run(self):
        """Executes the main game loop until a winner is determined"""
        while True:
            current_player = self.players[self.current_player]
            opponent = self.players[1 - self.current_player]

            print(f'\033[1m               {current_player.name}\'s turn:\033[0m')
            
            if current_player.name == "Player":
                print('\033[1m       Player`s Guess Board\033[0m')
                current_player.display.display_board(current_player.attack_board.grid)
                current_player.take_turn(opponent)
            else:
                current_player.take_turn(opponent)

            if opponent.ship_manager.all_ships_sunk():
                print("\n*******************************************")
                print(f"\033[1m       {current_player.name} has won the game!\033[0m")
                print("*******************************************\n")
                break

            self.current_player = 1 - self.current_player
            print('----------------------------------------------')

class GamePlay:
    """Main game coordinator"""
    def __init__(self):
        self.setup = GameSetup()
        self.players = self.setup.players
        self.game_loop = GameLoop(self.players)

    def display_welcome_message(self):
        """Displays game introduction and instructions"""
        print('----------------------------------------- Welcome to the game \033[1m"BATTLESHIP"\033[0m -----------------------------------------')
        print('\n\033[1m                                        OBJECTIVE\033[0m')
        print(config['instructions']['objective'])
        
        print('\n\033[1m                                         SETUP\033[0m')
        for setup_instruction in config['instructions']['setup']:
            print(setup_instruction)
        
        print("\n2. The fleet includes:\n")
        for ship, length in config['ships'].items():
            print(f" • 1 {ship} ({length} squares)")
        
        print('\n\033[1m                                        GAMEPLAY\033[0m')
        for gameplay_instruction in config['instructions']['gameplay']:
            print(gameplay_instruction)
        
        print('\n\033[1m                                        WINNING\033[0m')
        print(config['instructions']['winning'])
        print('\n')
        print('---------------------------------------------------------------------------------------------------------------')

    def run_game(self):
        """Coordinates the complete game flow"""
        self.display_welcome_message()  # Show introduction
        for player in self.players:
            self.setup.deploy_all_ships(player)  # Setup phase
        self.game_loop.run()  # Main game loop

if __name__ == "__main__":
    game = GamePlay()
    game.run_game()