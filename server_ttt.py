from socket import socket, AF_INET, SOCK_STREAM
import threading
from ttt import *

# Server for Tic Tac Toe game
#Constants
HOST = 'localhost'
PORT = 12345
ADDR = (HOST, PORT)

#create game class
class ttt_game():
    def __init__(self, p1_id: int, p1_socket):
        self.p1_id = p1_id
        self.p1_socket = p1_socket
        self.p2_socket = None
        self.p2_id = None
        self.board = [' ' for _ in range(9)]
        self.current_turn = p1_id
        self.score = {p1_id: 0}

    #Updates the board state
    def make_move(self, player_id: int, position: int):
        if self.board[position] == ' ' and player_id == self.current_turn:
            self.board[position] = 'X' if player_id == self.p1_id else 'O'
            self.current_turn = self.p2_id if player_id == self.p1_id else self.p1_id
            return True
        return False
    
    #checks if the board has a winner by matching the possibilities with the winning combinations
    def check_winner(self):
        winning_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
            (0, 4, 8), (2, 4, 6)              # diagonals
        ]
        for a, b, c in winning_combinations:
            if self.board[a] == self.board[b] == self.board[c] and self.board[a] != ' ':
                return self.board[a]
        return None
    
    #Resets the game board and current turn
    def reset_game(self, first : int):
        self.board = [' ' for _ in range(9)]
        self.current_turn = first

    #reset the scoreboard (unused)
    def reset_score(self):
        self.score = {self.p1_id: 0, self.p2_id: 0}

    #returns the current board state as a string
    def get_board(self):
        return f"{self.board[0]} | {self.board[1]} | {self.board[2]}\n" \
               f"--+---+--\n" \
               f"{self.board[3]} | {self.board[4]} | {self.board[5]}\n" \
               f"--+---+--\n" \
               f"{self.board[6]} | {self.board[7]} | {self.board[8]}\n" 
    
    #adds a player to the game (for p2 specifically)
    def add_player(self, player_id: int, p2_socket):
        if self.p2_id is None:
            self.p2_id = player_id
            self.p2_socket = p2_socket
            self.score[player_id] = 0
            print(f"Player {player_id} added to the game.")
        else:
            print("Game is already full. Cannot add more players.")

    
# Create a server socket
socket_server = socket(AF_INET, SOCK_STREAM)
socket_server.bind(ADDR)
socket_server.listen(5)
print(f"Server started on {HOST}:{PORT}")

# Dictionary to hold the threads for active games
active_game_threads = {} # (unused, but can be used to track active games)
curr_id = 0 # Global variable to keep track of player IDs
game_id = 0 # Global variable to keep track of game IDs
open_game = None #holds a reference to the open game if it exists

def handle_game(game):
    
    # Game Loop
    while True:
        # Define player sockets
        p1_socket = game.p1_socket
        p2_socket = game.p2_socket

        #Rest the game state
        game.reset_game(game.p1_id)

        #get and send the current game state
        game_state = game.get_board()
        send_message(p1_socket, 'game', game_state)
        send_message(p2_socket, 'game', game_state)

        #Match loop
        while True:
            # Check for draw condition
            if ' ' not in game.board:
                send_message(p1_socket, 'info', "It's a draw!")
                send_message(p2_socket, 'info', "It's a draw!")
                game.score[game.p1_id] += 1
                game.score[game.p2_id] += 1
                break
            # Wait for player moves
            try:
                #send action message to p1
                send_message(p1_socket, 'action', "Your turn to make a move.")

                # Read move from player 1
                move_data = read_message(p1_socket)
                if move_data is None:
                    send_message(p1_socket, 'error', "No move data received. Please try again.")
                    break
                move_data = move_data[0] #Messages are arrays, get the first (and only) message

                # Process move data
                if move_data:
                    m_type, move = move_data

                    #Handle exit message
                    if m_type == 'exit':
                        send_message(p1_socket, 'exit', 'Successfully exited the game.')
                        send_message(p2_socket, 'exit', 'Opponent exited the game.')
                        print(f"Player {game.p2_id} exited the game. Ending the game.")
                        p1_socket.close()
                        p2_socket.close()
                        return

                    elif m_type == 'move':
                        # Parse the move
                        row, col = map(int, move.split(','))

                        # Make the move on the game board
                        if game.make_move(game.p1_id, row * 3 + col):
                            send_message(p2_socket, 'move', f"Player {game.p1_id} made a move at position {move}.")
                            game_state = game.get_board()
                            send_message(p1_socket, 'game', game_state)
                            send_message(p2_socket, 'game', game_state)

                            # Check for a winner
                            if game.check_winner():
                                #Send win messages to both players
                                send_message(p1_socket, 'info', f"Player {game.p1_id} wins!")
                                send_message(p2_socket, 'info', f"Player {game.p1_id} wins!")

                                #Update scores
                                game.score[game.p1_id] += 2

                                # Reset the game state and notify players
                                send_message(p1_socket, 'info', "Game reset. Starting a new game...")
                                send_message(p2_socket, 'info', "Game reset. Starting a new game...")
                                break
                        else:
                            send_message(p1_socket, 'error', "Invalid move. Try again.")
                    else:
                        send_message(p1_socket, 'error', "Invalid message format. Expected 'move:row,col'.")
                
                # Check for draw condition after player 1's move
                if ' ' not in game.board:
                    send_message(p1_socket, 'info', "It's a draw!")
                    send_message(p2_socket, 'info', "It's a draw!")
                    game.score[game.p1_id] += 1
                    game.score[game.p2_id] += 1
                    break

                # Now it's player 2's turn
                #send action message to p2
                send_message(p2_socket, 'action', "Your turn to make a move.")

                # Read move from player 2
                move_data = read_message(p2_socket)
                if move_data is None:
                    send_message(p2_socket, 'error', "No move data received. Please try again.")
                    break
                move_data = move_data[0]

                # Process move data
                if move_data:
                    m_type, move = move_data

                    # Handle exit message
                    if m_type == 'exit':
                        send_message(p2_socket, 'exit', 'Successfully exited the game.')
                        send_message(p1_socket, 'exit', 'Opponent exited the game.')
                        print(f"Player {game.p2_id} exited the game. Ending the game.")
                        p1_socket.close()
                        p2_socket.close()
                        return
                    
                    # Handle move message
                    elif m_type == 'move':
                        # Parse the move
                        row, col = map(int, move.split(','))

                        # Make the move on the game board
                        if game.make_move(game.p2_id, row * 3 + col):
                            # Notify player 1 of player 2's move
                            send_message(p1_socket, 'move', f"Player {game.p2_id} made a move at position {move}.")

                            # Update and send the game state to both players
                            game_state = game.get_board()
                            send_message(p1_socket, 'game', game_state)
                            send_message(p2_socket, 'game', game_state)

                            # Check for a winner
                            if game.check_winner():
                                # Send win messages to both players
                                send_message(p1_socket, 'info', f"Player {game.p2_id} wins!")
                                send_message(p2_socket, 'info', f"Player {game.p2_id} wins!")

                                # Update scores and send them
                                game.score[game.p2_id] += 2

                                # Reset the game state and notify players
                                send_message(p1_socket, 'info', "Game reset. Starting a new game...")
                                send_message(p2_socket, 'info', "Game reset. Starting a new game...")
                                break
                        else:
                            send_message(p2_socket, 'error', "Invalid move. Try again.")
                    else:
                        send_message(p2_socket, 'error', "Invalid message format. Expected 'move:row,col'.")
            except Exception as e:
                print(f"Error handling game: {e}")
                send_message(p1_socket, 'error', "An error occurred during the game. Please try again.")
                send_message(p2_socket, 'error', "An error occurred during the game. Please try again.")
                break
        
        # After the game ends, update the scores and notify players
        send_message(p1_socket, 'score', f"Player {game.p1_id}: {game.score[game.p1_id]} | Player {game.p2_id}: {game.score[game.p2_id]}")
        send_message(p2_socket, 'score', f"Player {game.p1_id}: {game.score[game.p1_id]} | Player {game.p2_id}: {game.score[game.p2_id]}")


        
        
# Accepts a client connection and starts a game if two players are connected
def accept_client(client_socket, player_id):
    global active_game_threads, open_game, game_id
    print(f"Player {player_id} connected.")

    # Assign player ID
    if open_game is None:
        # Create a new game if no open game exists
        open_game = ttt_game(player_id, client_socket)
        send_message(client_socket, 'info', f"Welcome Player {player_id}. Waiting for another player to join...")
    else:
        # Add player to the existing game
        open_game.add_player(player_id, client_socket)

        # Notify both players that the second player has joined
        if open_game.p2_id is not None:
            send_message(client_socket, 'info', f"Welcome Player {player_id}. Starting the game...")
            send_message(open_game.p1_socket, 'info', f"Player {player_id} has joined the game. Starting the game...")

            # Start a new thread for the game
            game_thread = threading.Thread(target=handle_game, args=[open_game])
            game_thread.start()
            active_game_threads[game_id] = game_thread
            game_id += 1
            open_game = None


# Main server loop to accept client connections
while True:
    client_socket, addr = socket_server.accept()
    print(f"Connection from {addr} has been established.")
    
    # Assign a unique player ID
    curr_id += 1
    player_id = curr_id

    accept_client(client_socket, player_id)






    



    

