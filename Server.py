import socket
import threading
import time

# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT_TCP = 9999
SERVER_PORT_UDP = 5051

# Dictionary to store connected clients

port_Num={}
clients = {}
thread_Clients={}
hidden_Clients=[]


def send_video_chunks(video_data, res_Socket, chunk_size=1024):
    try:
       
        # Send the size of the video data first
        res_Socket.sendall(str(len(video_data)).encode().ljust(1024))
        
        # Split the video data into chunks and send each chunk
        for i in range(0, len(video_data), chunk_size):
            chunk = video_data[i:i+chunk_size]
            res_Socket.sendall(chunk)
    
    except Exception as e:
        print(f"Error occurred while sending video chunks: {e}")
    
    finally:
        # Close the client socket
        res_Socket.close()

def receive_video(client_socket):
    try:
        # Receive the size of the video data
        video_size = int(client_socket.recv(1024).strip())
        print(f"Receiving video data of size: {video_size} bytes")
        
        # Initialize an empty byte string to store the video data
        video_data = b''
        
        # Keep track of the total bytes received
        total_bytes_received = 0
        
        # Receive video data in chunks until the total bytes received equals the video size
        while total_bytes_received < video_size:
            # Receive a chunk of data from the server
            chunk = client_socket.recv(min(video_size - total_bytes_received, 1024))
            
            # If the chunk is empty, the server has finished sending the video
            if not chunk:
                break
            
            # Append the chunk to the video data
            video_data += chunk
            
            # Update the total bytes received
            total_bytes_received += len(chunk)
        
        print("Video data received successfully!")
        return video_data
    
    except Exception as e:
        print(f"Error occurred while receiving video: {e}")

def broadcast(sender_socket, sender_username, recipients, message_body):
    # Iterate through specified recipients and send the message to each one
    for recipient_username in recipients:
        if recipient_username in clients:
            recipient_socket = clients[recipient_username]
            try:
                # Save broadcast message to the sender's text file
                with open(f"{sender_username}.txt", "a") as sender_file:
                    sender_file.write(f"Broadcast to {', '.join(recipients)}: {message_body}\n")

                # Save broadcast message to each recipient's text file
                with open(f"{recipient_username}.txt", "a") as recipient_file:
                    recipient_file.write(f"Broadcast from {sender_username}: {message_body}\n")

                sender_socket.sendall(f"Broadcast sent to {', '.join(recipients)}.".encode())

            except Exception as e:
                print(f"Error occurred while broadcasting to {recipient_username}: {e}")
        else:
            sender_socket.sendall(f"Recipient {recipient_username} is not online.".encode())

# Function to handle TCP connections from clients
def handle_tcp_client(client_socket, client_address):
    print(f"[TCP] New connection from {client_address}")
    client_socket.sendall("Successful".encode())
    print("Successful connection sending acknowledgement...")
    # Receive client's username
    username = client_socket.recv(1024).decode()
    if "1" in username:
        thread_Clients[username]=client_socket
        print("Its a thread.")
    else:
        clients[username] = client_socket

    print("new Client User name:",username)
    
    #sending to acknowledgement to client
    menu_options = """
Menu Options:
1. View Online Users
2. Send Media(text or Video)
3. View Messages
4. Hide Online Status
5. Unhide Online Status
6. Broadcast message
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

                elif message.startswith("/txt "):
                        print("trying to send...")
                        recipient, message_body = message.split(maxsplit=1)[1].split(maxsplit=1)
                        print(recipient)
                        newres = recipient + "1"
                        print(newres)
                        print(message_body)
                        
                        if newres in thread_Clients:
                            recipient_socket = thread_Clients[newres]
                            # Send the type of data ("txt")
                            recipient_socket.sendall("txt".encode())
                            
                            # Wait for acknowledgment from the recipient
                            time.sleep(2)
                           
                            # If acknowledgment received, send the message body

                                # Send the message body
                            recipient_socket.sendall(f"Message from {username}: {message_body}".encode())
                            client_socket.sendall("Message delivered.".encode())
                        else:
                            client_socket.sendall("Recipient is not online.".encode())

                elif message.startswith("/video "):
                    recipient, message_body = message.split(maxsplit=1)[1].split(maxsplit=1)
                    newres = recipient + "1"
                    client_socket.sendall("ACK".encode())
                    video_data=receive_video(client_socket)
                    if newres in thread_Clients:
                            recipient_socket = thread_Clients[newres]
                            recipient_socket.sendall(f"video {message_body}".encode())
                            # Wait for acknowledgment from the recipient
                            time.sleep(2)

                            send_video_chunks(video_data,recipient_socket)

                elif message.startswith("/hide "):
                    recipient, message_body = message.split(maxsplit=1)[1].split(maxsplit=1)
                    hidden_Clients.append(recipient)

                elif message.startswith("/unhide "):
                    recipient, message_body = message.split(maxsplit=1)[1].split(maxsplit=1)
                    if recipient in hidden_Clients:
                        hidden_Clients.remove(recipient)

                elif message.startswith("/exit "):
                    recipient, message_body = message.split(maxsplit=1)[1].split(maxsplit=1)
                    del clients[recipient]

                elif message.startswith("/broadcast "):
                    _, recipients_str, broadcast_message = message.split(maxsplit=2)
                    recipients = recipients_str.split()
                    broadcast(client_socket, username, recipients, broadcast_message)

        except Exception as e:
            print(f"[TCP] Error: {e}")
            del clients[username]
            break


# Function to send a list of online users to the requesting client
def send_online_users(client_socket):
    # Filter clients' keys to exclude those in the HiddenClient array
    if len(hidden_Clients)==len(clients):
        client_socket.sendall("Noone is Online!!!".encode())
    else:
        online_users = ", ".join([username for username in clients.keys() if username not in hidden_Clients])

        client_socket.sendall(online_users.encode())

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