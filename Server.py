import socket
import threading

# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT_TCP = 9999
SERVER_PORT_UDP = 5051

# Dictionary to store connected clients
clients = {}

# Function to handle TCP connections from clients
def handle_tcp_client(client_socket, client_address):
    print(f"[TCP] New connection from {client_address}")
    client_socket.sendall("Successful".encode())
    print("Successful connection sending acknowledgement...")
    # Receive client's username
    username = client_socket.recv(1024).decode()
    clients[username] = client_socket

    print("new Client User name:",username)
    
    #sending to acknowledgement to client
    menu_options = """
Menu Options:
1. View Online Users
2. Send Message
3. View Messages
4. Hide Online Status
5. Exit
"""
    client_socket.sendall(menu_options.encode())

   
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if message:
                if message == "1":
                    send_online_users(client_socket)
                elif message=="2": 
                    del clients[username ]
                    client_socket.sendall("Client is now Offline".encode())
                    # broadcast(message, username)
                elif message.startswith("/msg "):
                    print("trying to send...")
                    recipient, message_body = message.split(maxsplit=1)[1].split(maxsplit=1)
                    print(recipient)
                    print(message_body)
                    if recipient in clients:
                        recipient_socket = clients[recipient]
                        recipient_socket.sendall(f"Message from {username}: {message_body}".encode())
                        client_socket.sendall("Message delivered.".encode())
                    else:
                        client_socket.sendall("Recipient is not online.".encode())
 
        except Exception as e:
            print(f"[TCP] Error: {e}")
            del clients[username]
            break

# Function to broadcast message to all connected clients
def broadcast(message, sender):
    for username, client_socket in clients.items():
        if username != sender:
            try:
                client_socket.sendall(message.encode())
            except Exception as e:
                print(f"[TCP] Error broadcasting message to {username}: {e}")
                del clients[username]

# Function to send a list of online users to the requesting client
def send_online_users(client_socket):
    online_users = ", ".join(clients.keys())
    client_socket.sendall(online_users.encode())

# Function to handle UDP connections for media streaming (not implemented)
def handle_udp_client():
    pass

# Main function to start the server
def main():
    # Create TCP server socket
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.bind((SERVER_HOST, SERVER_PORT_TCP))
    tcp_server_socket.listen(5)
    print(f"[TCP] Server listening on {SERVER_HOST}:{SERVER_PORT_TCP}")

    # Create UDP server socket
    udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server_socket.bind((SERVER_HOST, SERVER_PORT_UDP))
    print(f"[UDP] Server listening on {SERVER_HOST}:{SERVER_PORT_UDP}")

    # Listen for incoming TCP connections
    while True:
        client_socket, client_address = tcp_server_socket.accept()
        client_thread = threading.Thread(target=handle_tcp_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    main()
