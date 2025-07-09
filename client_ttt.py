from socket import socket, AF_INET, SOCK_STREAM
from ttt import *

#client for tic-tac-toe game
#Constants
HOST = 'localhost'
PORT = 12345
ADDR = (HOST, PORT)
    

def make_move(row, col):
    """
    Sends a move to the server.
    
    :param row: Row index for the move (0-2).
    :param col: Column index for the move (0-2).
    """
    move = f"{row},{col}"
    send_message(server_socket, 'move', move)

server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.connect(ADDR)
print(f"Connected to server at {HOST}:{PORT}")

while True:
    # Receive messages from the server
    messages = read_message(server_socket)
    if messages is None:
        print("No messages received. Exiting.")
        break
    for msg in messages:
        if not msg:
            continue
        m_type, data = msg
        if not data:
            break  # Exit if no data is received
        if m_type == 'info':
            print(f"Info: {data}")
        elif m_type == 'error':
            print(f"Error: {data}")
        elif m_type == 'move':
            print(f"Move: {data}")
        elif m_type == 'game':
            print(f"Game State:\n{data}")
        elif m_type == 'score':
            print(f"Scoreboard:\n{data}")
        elif m_type == 'exit':
            print(f"Exit: {data}")
            server_socket.close()
            exit(0)
        elif m_type == 'action':
            # action message tells player to make a move
            move = input("Enter your move (row,col) or 'exit': ")
            if move.lower() == 'exit':
                print("Exiting the game.")
                send_message(server_socket, 'exit', 'Player exited the game.')
                continue
            while True:
                try:
                    row, col = map(int, move.split(','))
                    if 0 <= row < 3 and 0 <= col < 3:
                        make_move(row, col)
                        break
                    else:
                        print("Invalid move. Please enter row and column as numbers between 0 and 2.")
                except ValueError:
                    print("Invalid input. Please enter row and column as numbers separated by a comma (e.g., 1,2).")
        else:
            print(f"Unknown message type: {m_type}")




