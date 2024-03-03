import socket
import threading
import time
import select
import os

# Server configuration
SERVER_IP = '127.0.0.1'
SERVER_PORT = 9999

logged_In = False
peer_udp_socket = None
peer_udp_address = None
udp_address_ready_event = threading.Event()
username1=""


def receive_video_chunks(client_socket, output_file,usr):
    try:
        # Receive the size of the video data
        video_size = int(client_socket.recv(1024).strip())
        print(output_file)
        print(f"Receiving video data of size: {video_size} bytes")
        newname = "Sent_To_"+usr+output_file
        # Open the output file in binary write mode
        with open(newname, 'wb') as f:
            # Receive video data in chunks until all data is received
            received_size = 0
            while received_size < video_size:
                # Receive a chunk of data
                chunk = client_socket.recv(1024)
                received_size += len(chunk)
                
                # Write the chunk to the output file
                f.write(chunk)

        print("Video data received successfully and written to file:", newname)
    
    except Exception as e:
        print(f"Error occurred while receiving video chunks: {e}")
    
    
def send_video(client_socket, video_filename, chunk_size=1024):
    try:
        video_size = os.path.getsize(video_filename)
        print(f"Sending video data of size: {video_size} bytes")
        
        # Send the size of the video data to the client
        client_socket.sendall(str(video_size).encode())
        # Open the video file in binary mode
        with open(video_filename, 'rb') as video_file:
            while True:
                # Read a chunk of data from the video file
                chunk = video_file.read(chunk_size)
                print(chunk)
                
                # If the chunk is empty, we've reached the end of the file
                if not chunk:
                    break
                
                # Send the chunk to the client
                client_socket.sendall(chunk)
    
    except FileNotFoundError:
        print(f"Error: File '{video_filename}' not found.")
    except Exception as e:
        print(f"Error occurred while sending video: {e}")


def connect_to_server(username):
    try:
        # Client TCP socket setup
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")
        f =(client_socket.recv(1024).decode('utf-8'))
        usr =username
        username+="1"
        client_socket.send(username.encode('utf-8'))
        
        while True:
            try:
                if client_socket is not None:
                    ready = select.select([client_socket.fileno()],[],[],0)  # Timeout set to 5 seconds
                    if ready[0]:
                       
                        msg = client_socket.recv(1024).decode('utf-8')
                    
                        if msg == "txt":
                            mess = client_socket.recv(1024).decode('utf-8')
                            with open(usr+".txt", "a") as file:
                                file.write(mess + '\n')
                        elif msg.startswith ("video "):
                            filename =msg.split()[1]
                           
                            receive_video_chunks(client_socket,filename,usr)
                             
                else:
                    print("Client socket is None. Exiting UDP operations.")
                    break
            except Exception as e:
                print(f"An error occurred in UDP operations: {e}")
                break

    except ConnectionRefusedError:
        print("Connection to server failed. Please make sure the server is running.")
        exit(1)
    finally:
        # Close the socket to prevent resource leaks
        if client_socket:
            client_socket.close()


def manage_p2p_communications():
    global peer_udp_socket, peer_udp_address, udp_address_ready_event
    try:
        # Peer-2-peer UDP communication setup
        peer_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        peer_udp_socket.bind(('127.0.0.1', 0))  # Binding to a specific port
        peer_udp_address = peer_udp_socket.getsockname()
        print(f"UDP socket bound to address: {peer_udp_address}")

        udp_address_ready_event.set()  # Set the event to indicate UDP address is ready

        while True:
            try:
                data, addr = peer_udp_socket.recvfrom(1024)
                message = data.decode('utf-8')
                print(f"Received from {addr}: {message}")  # Print received data
                
                # Write the received message to a text file
                with open("received_messages.txt", "a") as file:
                    file.write(f"Received from {addr}: {message}\n")

                # Send acknowledgment back to the client
                acknowledgment_message = "Data received successfully"
                peer_udp_socket.sendto(acknowledgment_message.encode('utf-8'), addr)

            except socket.error as e:
                print(f"Socket error: {e}")

    except OSError as e:
        print(f"Error: {e}")

    finally:
        peer_udp_socket.close()
        print("Peer connection closed.")

def run_client():
    global logged_In, peer_udp_address, udp_address_ready_event

    try:
        # Client TCP socket setup
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")
        c=(client_socket.recv(1024).decode('utf-8'))

    
        menu = ""
        usr=""
        m ="null"
        while True:
            if not logged_In:
                user_input = input("Enter command (/register [username] or /login): ")
               

            else:
                print(menu)
                user_input = input("Choose an option from the Menu: ")

            if user_input.startswith("register ") or user_input.startswith("/login "):
                # Reset login status before sending registration or login command
                usr = user_input.split(" ")[1]

                udpOP = threading.Thread(target=connect_to_server,args=(usr,))
                udpOP.start()
                print(usr)

                client_socket.send(usr.encode('utf-8'))
                client_socket.sendall(f"UDP {peer_udp_address[0]} {peer_udp_address[1]}".encode())

                menu = client_socket.recv(1024).decode('utf-8')
                if menu:
                    logged_In = True
                    print("Successfully registered. Your username is", usr)

            elif logged_In and user_input == "1":
                client_socket.send(user_input.encode('utf-8'))
                users = "Online Users:\n---------------------------------\n"
                users += client_socket.recv(1024).decode('utf-8')
                print(users)

            elif logged_In and user_input == "2":
                try:
                    recipient = input("Enter recipient's username: ")
                    type = input("Enter type of data to send, video or txt: ")
                    types="video,txt"
                    while True:
                        if type in types:
                            break
                        type = input("""Please Enter any of these types-> "video or txt:"" """)

                    if type=="txt":
                        message = input("Enter message: ")

                    # Send a request to the server for UDP information
                        client_socket.send(f"/txt {recipient} {message}".encode('utf-8'))

                        # Receive the UDP information from the server
                        udp_info = client_socket.recv(1024).decode('utf-8')
                        # print(udp_info)

                    elif type =="video":
                        filname = input("enter file name: ")
                        client_socket.send(f"/video {recipient} {filname}".encode('utf-8'))
                        ac=client_socket.recv(1024).decode('utf-8')
                        if ac=="ACK":
                            
                            send_video(client_socket,filname)
                    
                except ValueError as ve:
                    print(f"Error: {ve}. Please check the format of the received UDP information.")
                
                except socket.error as se:
                    print(f"Socket error: {se}. There might be an issue with the socket connection.")
                
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")

            elif logged_In and user_input == "3":
              # Read and display the text file content
                txt_file = usr + ".txt"
                if os.path.exists(txt_file):
                    with open(txt_file, "r") as file:
                        file_content = file.read()
                        if file_content:
                            print(file_content)
                        else:
                            print("No messages found.")
                else:
                    print("No messages found.")
            
            elif logged_In and user_input == "4":
                client_socket.send(f"/hide {usr} {m}".encode('utf-8'))
                print("your online status is now Hidden")

               
            elif logged_In and user_input=="5":
                client_socket.send(f"/unhide {usr} {m}".encode('utf-8'))
                print("your online status can be seen by everyone")

            elif logged_In and user_input == "6":
                try:
                    recipients_str = input("Enter list of recipients (space-separated usernames): ")
                    broadcast_message = input("Enter broadcast message: ")
                    client_socket.send(f"/broadcast {recipients_str} {broadcast_message}".encode('utf-8'))

                except Exception as e:
                    print(f"An unexpected error occurred: {e}")

            else:
                print("Invalid command.")

    except KeyboardInterrupt:
        print("Client terminated.")

    finally:
        if client_socket:
            client_socket.close()


if __name__ == "__main__":
    udp_thread = threading.Thread(target=manage_p2p_communications)
    tcp_thread = threading.Thread(target=run_client)
    
    # Start both threads
    udp_thread.start()
    tcp_thread.start()

    # Wait for both threads to finish
    udp_thread.join()
    tcp_thread.join()
