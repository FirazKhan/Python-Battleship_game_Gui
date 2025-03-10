import tkinter as tk
from tkinter import ttk
from edit_this import (
    GameSetup, 
    SHIP_TYPES, 
    BOARD_SIZE, 
    LETTERS_TO_NUMS
)

class WindowManager:
    """Handles window positioning and styling"""
    @staticmethod
    def center_window(window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() - width) // 2
        y = (window.winfo_screenheight() - height) // 2
        window.geometry(f'+{x}+{y}')

    @staticmethod
    def create_styles():
        style = ttk.Style()
        style.configure('Ship.TButton', background='green')
        style.configure('Hit.TButton', background='red')
        style.configure('Miss.TButton', background='blue')

class GameDisplay:
    """Handles all game UI elements"""
    def __init__(self, parent):
        # Setup phase frame
        self.setup_frame = ttk.Frame(parent, padding="10")
        self.setup_frame.grid(row=0, column=0)
        
        # Create placement board
        self.create_placement_board()
        self.create_setup_controls()
        
        # Game phase frame
        self.game_frame = ttk.Frame(parent, padding="10")
        self.game_frame.grid(row=0, column=0)
        self.create_game_boards()
        self.game_frame.grid_remove()

    def create_placement_board(self):
        placement_frame = ttk.LabelFrame(self.setup_frame, text="Place Your Ships")
        placement_frame.grid(row=0, column=0, padx=5, pady=5)
        
        self.placement_buttons = [[
            ttk.Button(placement_frame, width=3)
            for _ in range(BOARD_SIZE)
        ] for _ in range(BOARD_SIZE)]
        
        for i, row in enumerate(self.placement_buttons):
            for j, btn in enumerate(row):
                btn.grid(row=i, column=j, padx=1, pady=1)

    def create_setup_controls(self):
        self.orientation = tk.StringVar(value="H")
        controls = ttk.Frame(self.setup_frame, padding="10")
        controls.grid(row=1, column=0)
        
        ttk.Radiobutton(controls, text="Horizontal", variable=self.orientation, 
                       value="H").grid(row=0, column=0, sticky='w')
        ttk.Radiobutton(controls, text="Vertical", variable=self.orientation, 
                       value="V").grid(row=1, column=0, sticky='w')
        
        self.message_label = ttk.Label(controls, text="Place your ships")
        self.message_label.grid(row=2, column=0)
        
        self.start_button = ttk.Button(controls, text="Start Game", state='disabled')
        self.start_button.grid(row=3, column=0)

    def create_game_boards(self):
        # Player's board
        player_frame = ttk.LabelFrame(self.game_frame, text="Your Guesses")
        player_frame.grid(row=0, column=0, padx=5)
        
        self.player_buttons = [[
            ttk.Button(player_frame, width=3)
            for _ in range(BOARD_SIZE)
        ] for _ in range(BOARD_SIZE)]
        
        # Computer's board
        computer_frame = ttk.LabelFrame(self.game_frame, text="Computer's Guesses")
        computer_frame.grid(row=0, column=1, padx=5)
        
        self.computer_buttons = [[
            ttk.Button(computer_frame, width=3)
            for _ in range(BOARD_SIZE)
        ] for _ in range(BOARD_SIZE)]
        
        # Set up grid
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                self.player_buttons[i][j].grid(row=i, column=j, padx=1, pady=1)
                self.computer_buttons[i][j].grid(row=i, column=j, padx=1, pady=1)
        
        self.game_message = ttk.Label(self.game_frame, text="")
        self.game_message.grid(row=1, column=0, columnspan=2)

class BattleshipGUI:
    """Main game coordinator"""
    def __init__(self, root):
        self.root = root
        self.root.title("Battleship")
        
        WindowManager.center_window(self.root)
        WindowManager.create_styles()
        
        self.setup_new_game()

    def setup_new_game(self):
        # Initialize game components
        self.setup = GameSetup()
        self.players = self.setup.players
        self.display = GameDisplay(self.root)
        
        # Set up placement phase
        self.current_ship_index = 0
        self.ships_to_place = list(SHIP_TYPES.items())
        
        # Bind events
        self.bind_placement_buttons()
        self.bind_game_buttons()
        self.display.start_button.configure(command=self.start_game)

    def bind_placement_buttons(self):
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                self.display.placement_buttons[i][j].configure(
                    command=lambda x=i, y=j: self.try_place_ship(x, y))

    def bind_game_buttons(self):
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                self.display.player_buttons[i][j].configure(
                    command=lambda x=i, y=j: self.make_move(x, y))

    def try_place_ship(self, row, col):
        if self.current_ship_index >= len(self.ships_to_place):
            return
            
        ship, length = self.ships_to_place[self.current_ship_index]
        orientation = self.display.orientation.get()
        
        # Use player's validation methods
        player = self.players[0]
        if player.validator.validate_placement(length, row, col, orientation):
            if not player.validator.check_overlap(player.ship_manager.grid, row, col, orientation, length):
                player.ship_manager.deploy_ship(ship, length, row, col, orientation)
                self.update_placement_board()
                self.advance_ship_placement()

    def advance_ship_placement(self):
        self.current_ship_index += 1
        if self.current_ship_index >= len(self.ships_to_place):
            self.display.message_label.config(text="All ships placed! Click Start Game")
            self.display.start_button.config(state='normal')
        else:
            ship, length = self.ships_to_place[self.current_ship_index]
            self.display.message_label.config(text=f"Place your {ship} (length: {length})")

    def update_placement_board(self):
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.players[0].ship_manager.grid[i][j] == "X":
                    self.display.placement_buttons[i][j].config(style='Ship.TButton')

    def make_move(self, row, col):
        human = self.players[0]
        computer = self.players[1]

        # Player's turn
        if human.attack_board.grid[row][col] in ["-", "X"]:
            self.display.game_message.config(text="Already attacked this position!")
            return

        hit = computer.ship_manager.grid[row][col] == "X"
        human.attack_board.grid[row][col] = "X" if hit else "-"
        self.display.player_buttons[row][col].config(
            style='Hit.TButton' if hit else 'Miss.TButton')

        if hit:
            computer.ship_manager.check_sunk_ship(row, col)
            if computer.ship_manager.all_ships_sunk():
                self.show_game_over("Player")
                return

        # Computer's turn
        computer.take_turn(human)
        self.update_computer_board()
        
        if human.ship_manager.all_ships_sunk():
            self.show_game_over("Computer")

    def update_computer_board(self):
        computer = self.players[1]
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if computer.attack_board.grid[i][j] in ["-", "X"]:
                    self.display.computer_buttons[i][j].config(
                        style='Hit.TButton' if computer.attack_board.grid[i][j] == "X" else 'Miss.TButton')

    def start_game(self):
        self.setup.deploy_all_ships(self.players[1])
        self.display.setup_frame.grid_remove()
        self.display.game_frame.grid()
        self.display.game_message.config(text="Game started! Make your move")

    def show_game_over(self, winner):
        popup = tk.Toplevel(self.root)
        popup.title("Game Over")
        popup.transient(self.root)
        popup.grab_set()
        
        message = ttk.Label(popup, text=f"Game Over! {winner} wins!", 
                          font=('Arial', 14, 'bold'), padding=20)
        message.pack()
        
        play_again_btn = ttk.Button(popup, text="Play Again", 
                                  command=lambda: self.restart_game(popup))
        play_again_btn.pack(pady=10)
        
        WindowManager.center_window(popup)

    def restart_game(self, popup):
        # Destroy the popup
        popup.destroy()
        
        # Remove old game frames
        if hasattr(self, 'display'):
            self.display.setup_frame.destroy()
            self.display.game_frame.destroy()
        
        # Setup new game
        self.setup_new_game()

def main():
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.minsize(600, 400)
    WindowManager.center_window(root)
    root.mainloop()

if __name__ == "__main__":
    main()