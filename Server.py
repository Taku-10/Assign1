import socket
import threading

# Server configuration
SERVER_IP = '127.0.0.1' 
SERVER_PORT = 5050

# Maintain a list of active clients
active_clients = []

# Dictionary to store client information (username: client_socket)
client_info = {}

# Server socket setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen()

def manage_client_connections(client_socket, address):
    try:
        # Initialize the client as not logged in
        logged_in = False

        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break  # Connection closed by client

            if data.startswith("/list"):
                if logged_in:
                    user_list = "\n".join(client_info.values())
                    client_socket.send(f"Available users:\n{user_list}".encode('utf-8'))
                else:
                    client_socket.send("Please log in or register first.".encode('utf-8'))
                continue

            # Check for registration command
            elif data.startswith("register"):
                if not logged_in:
                    username = data.split(" ", 1)[1]
                    register_new_client(username, client_socket)
                    logged_in = True
                else:
                    client_socket.send("You are already logged in.".encode('utf-8'))
                continue

            # Check for login command
            elif data.startswith("/login "):
                if not logged_in:
                    username = data.split(" ", 1)[1]
                    login_client(username, client_socket)
                    logged_in = True
                else:
                    client_socket.send("You are already logged in.".encode('utf-8'))
                continue

            # Check if the client is logged in before processing further commands
            if not logged_in:
                client_socket.send("Please log in or register first.".encode('utf-8'))
                continue

            # Check for command structure for direct messaging
            elif data.startswith("/msg "):
                command_parts = data.split(" ", 2)
                if len(command_parts) == 3:
                    target_username = command_parts[1]
                    message = command_parts[2]
                    
                    send_direct_message(client_socket, target_username, message)
                else:
                    client_socket.send("Invalid /msg command. Usage: /msg <username> <message>".encode('utf-8'))
                continue

            # Broadcast the message to all connected clients
            elif data.startswith("/broadcast "):
                send_message_to_all(f"{client_info[client_socket]}: {data[11:]}")  # Extract message after "/broadcast"
                continue

            # Handle other commands or broadcast messages
            send_message_to_all(f"{client_info[client_socket]}: {data}")

    except ConnectionResetError:
        pass
    finally:
        remove_client(client_socket)
        client_socket.close()

def register_new_client(username, client_socket):
    # Register a new client with the specified username
    if username not in client_info.values():
        client_info[client_socket] = username
        active_clients.append(client_socket)
        client_socket.send(f"Successfully registered as {username}".encode('utf-8'))
    else:
        client_socket.send(f"Username {username} is already taken. Please choose another.".encode('utf-8'))

def login_client(username, client_socket):
    # Log in an existing client with the specified username
    if username in client_info.values():
        client_info[client_socket] = username
        active_clients.append(client_socket)
        client_socket.send(f"Successfully logged in as {username}".encode('utf-8'))
    else:
        client_socket.send(f"Username {username} not found. Please register first.".encode('utf-8'))

def remove_client(client_socket):
    # Remove a client from the active clients list
    if client_socket in active_clients:
        del client_info[client_socket]
        active_clients.remove(client_socket)

def send_direct_message(sender_socket, target_username, message):
    # Send a direct message from one client to another
    for client_socket, username in client_info.items():
        if username == target_username:
            client_socket.send(f"Direct message from {client_info[sender_socket]}: {message}".encode('utf-8'))
            return
    sender_socket.send(f"User {target_username} not found.".encode('utf-8'))

def send_message_to_all(message):
    # Broadcast a message to all connected clients
    for client in active_clients:
        try:
            client.send(message.encode('utf-8'))
        except BrokenPipeError:
            pass

def run_server():
    print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

    while True:
        client_socket, address = server_socket.accept()
        print(f"New connection from {address}")
        
        active_clients.append(client_socket)

        # Handle each client in a separate thread
        client_thread = threading.Thread(target=manage_client_connections, args=(client_socket, address))
        client_thread.start()

if __name__ == "__main__":
    run_server()