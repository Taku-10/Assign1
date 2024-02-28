import socket
import threading

# Server configuration
SERVER_IP = '127.0.0.1'  
SERVER_PORT = 9999

# Client socket setup
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))

# Peer-2-peer UDP communication setup
peer_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

logged_in = False

def manage_server_responses():
    global logged_in
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            print(data)

            # Check if login was successful
            if data.startswith("Successfully logged in"):
                logged_in = True

            # Check if registration was successful
            elif data.startswith("Successfully registered"):
                logged_in = True
            else:
                logged_in = False
    except ConnectionResetError:
        print("Connection to server closed.")

def manage_p2p_communications():
    try:
        while True:
            data, addr = peer_udp_socket.recvfrom(1024)
            print(f"Received from {addr}: {data.decode('utf-8')}")
    except ConnectionResetError:
        print("Peer connection closed.")

def run_client():
    global logged_in
    print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

    server_thread = threading.Thread(target=manage_server_responses)
    peer_thread = threading.Thread(target=manage_p2p_communications)

    server_thread.start()
    peer_thread.start()

    try:
        while True:
            if not logged_in:
                user_input = input("Enter command (e.g., /register or /login): ")
            else:
                user_input = input("Enter command or message (/msg for direct message, /broadcast for broadcast, /list for user list): ")

            if user_input.startswith("register ") or user_input.startswith("/login "):
                # Reset login status before sending registration or login command
                logged_in = False
                client_socket.send(user_input.encode('utf-8'))
            elif logged_in and user_input.startswith("/msg "):
                client_socket.send(user_input.encode('utf-8'))
            elif logged_in and user_input.startswith("/broadcast "):
                client_socket.send(user_input.encode('utf-8'))
            elif logged_in and user_input.startswith("/list"):
                client_socket.send(user_input.encode('utf-8'))
            elif user_input.lower() == "/exit":
                client_socket.send(user_input.encode('utf-8'))
                break  
            else:
                print("Invalid command.")
    except KeyboardInterrupt:
        print("Client terminated.")
    finally:
        client_socket.close()
        peer_udp_socket.close()

if __name__ == "__main__":
    run_client()