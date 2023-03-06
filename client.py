"""This is the client side of the chat application. 
It is responsible for sending and receiving messages to/from the server."""

import socket
import struct
import threading
import select
import time


SERVER_HOST = "localhost"
SERVER_PORT = 7878

MULTICAST_GROUP = "224.0.0.1"
MULTICAST_PORT = 5000


tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
tcp_client.connect((SERVER_HOST, SERVER_PORT))

udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_client.bind(("", tcp_client.getsockname()[1]))
udp_client.connect((SERVER_HOST, SERVER_PORT))

multicast_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
multicast_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
multicast_client.bind(("", MULTICAST_PORT))

group = socket.inet_aton(MULTICAST_GROUP)
mreq = struct.pack('=4sl', group, socket.INADDR_ANY)
multicast_client.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


def receive():
    while True:
        try:
            ready_clients, _, _ = select.select([tcp_client, udp_client, multicast_client], [], [])
        except (KeyboardInterrupt, EOFError):
            exit()

        if udp_client in ready_clients:
            try:
                message, _ = udp_client.recvfrom(1024)
                print("<udp> ", message.decode("ascii"))
            except ConnectionResetError:
                print("<udp> An ConnectionResetError error occured!")
                exit()
            except Exception:
                exit()
                
        if tcp_client in ready_clients:
            try:
                message = tcp_client.recv(1024).decode("ascii")
                print("<tcp> ", message)
            except ConnectionResetError:
                print("<tcp> An ConnectionResetError error occured!")
                tcp_client.close()
                break
        
        if multicast_client in ready_clients:
            try:
                message, _ = multicast_client.recvfrom(1024)
                print("<multicast> ", message.decode("ascii"))
            except ConnectionResetError:
                print("<multicast> An ConnectionResetError error occured!")
                multicast_client.close()
                break


def write():
    print("Write your messages in given formats: \n tcp: @to message, \n udp: u message")
    try:
        while True:
            try:
                client_input = input(">")
            except (KeyboardInterrupt, EOFError):
                tcp_client.close()
                udp_client.close()
                multicast_client.close()
                exit()
                
            if not client_input:
                continue
            elif client_input.lower().startswith("u"):
                udp_client.sendto(client_input[1:].encode("ascii"), (SERVER_HOST, SERVER_PORT))
            elif client_input.lower().startswith("m"):
                multicast_client.sendto(client_input[1:].encode("ascii"), (MULTICAST_GROUP, MULTICAST_PORT))
            else:
                message = f'{nickname}: {client_input}'
                tcp_client.send(message.encode("ascii"))
            # Pause the thread to give the terminal to the receive function
            time.sleep(0.1)
    except (KeyboardInterrupt, EOFError):
        exit()


while True:
    try:
        nickname = input("Choose your nickname (must be longer than 2 letters): ")
    except (KeyboardInterrupt, EOFError):
        exit()
    
    tcp_client.send(f'{nickname}'.encode("ascii"))

    response = tcp_client.recv(1024).decode("ascii")
    if response.startswith("OK"):
        break
    else:
        print(response)


write_thread = threading.Thread(target=write, daemon=True)
write_thread.start()
receive()

