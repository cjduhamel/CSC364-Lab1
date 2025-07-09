def send_message(sock, message_type, message):
    """
    Sends a formatted message to the client socket.
    Message Types:
        - 'info' - Informational messages
        - 'error' - Error messages
        = 'move' - Player move messages
        - 'game' - Game state messages
        - 'score' - Scoreboard messages
        - 'exit' - Exit messages

    :param sock: The socket to send the message to.
    :param message_type: Type of the message (info, error, move, game).
    :param message: The message content to send.
    """

    formatted_message = f"{message_type}:{message}\t"
    sock.send(formatted_message.encode())

def read_message(sock):
    """
    Reads a message from a socket.

    Buffers the incoming data, as multiple messages can be read with a single .recv() call.
    Messages are tab separated to allow for newline characters in the data itself (e.g. game state).
    
    :param server_socket: The socket to read the message from.
    :return: An array of tuples containing the message types and data. 
    """
    buffer = sock.recv(1024).decode().strip()
    
    if not buffer:
        return None
    
    messages = buffer.split('\t')
    result = []
    for msg in messages:
        m_type, data = msg.split(':', 1)
        result.append((m_type, data))

    return result
    
    