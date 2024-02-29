import socket
import threading
import select

# Server configuration
SERVER_IP = '127.0.0.1'  
SERVER_PORT = 9999

logged_in = False

def connect_to_server():
    global client_socket
    try:
        # Client socket setup
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")
        print(client_socket.recv(1024).decode('utf-8'))
    except ConnectionRefusedError:
        print("Connection to server failed. Please make sure the server is running.")
        exit(1)

def manage_server_responses():
    print("Inside manage Server now")
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
    except ConnectionResetError:
        print("Connection to server closed.")

def manage_p2p_communications():
    global peer_udp_socket
    try:
        # Peer-2-peer UDP communication setup
        peer_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            try:
                data, addr = peer_udp_socket.recvfrom(1024)
                print(f"Received from {addr}: {data.decode('utf-8')}")
            except OSError as e:
                if e.errno == 10022:
                    print("Error: An invalid argument was supplied.")
                else:
                    raise e
    except ConnectionResetError:
        print("Peer connection closed.")

def run_client():
    global logged_in, client_socket, peer_udp_socket

    connect_to_server()

    # server_thread = threading.Thread(target=manage_server_responses)
    # peer_thread = threading.Thread(target=manage_p2p_communications)

    # server_thread.start()
    # peer_thread.start()

    try:
        menu=""
        messages=""
        while True:
            if not logged_in:
                user_input = input("Enter command (register <username> or /login): ")
            else:
                print(menu)
                user_input = input("Choose an option from the Menu: ")

            if user_input.startswith("register ") or user_input.startswith("/login "):
                # Reset login status before sending registration or login command
                usr = user_input.split(" ")[1]
                print(usr)
                
                client_socket.send(usr.encode('utf-8'))
                menu = client_socket.recv(1024).decode('utf-8')
                if menu:
                    logged_in=True
                    print("Succefully registered you username is: ",usr)
                    


            elif logged_in and user_input=="1":
                client_socket.send(user_input.encode('utf-8'))
                users ="Online Users:\n---------------------------------\n"
                users +=client_socket.recv(1024).decode('utf-8')
                print(users)
            elif logged_in and user_input=="2":
                recipient=input("Enter reciever's username: ")
                message =input("Enter message: ")
               
                client_socket.send(f"/msg {recipient} {message}".encode('utf-8'))
                delivery_confirmation = client_socket.recv(1024).decode('utf-8')
                print(delivery_confirmation)

            elif logged_in and user_input=="3":
                ready = select.select([client_socket], [], [], 5)  # Timeout set to 10 seconds
                if ready[0]:
                    msg = client_socket.recv(1024).decode('utf-8')
                    messages= messages+msg+'\n'
                    
                print(messages)


            elif logged_in and user_input=="4":
                client_socket.send(user_input.encode('utf-8'))
            elif user_input == "5":
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
