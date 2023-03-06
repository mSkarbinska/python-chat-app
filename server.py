"""_summary_: This file contains code for running chat server handling TCP and UDP connections."""

import socket
import threading


HOST = "localhost"
PORT = 7878

clients = []
nicknames = []


def main():
    try:
        threads = []
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        tcp_socket.bind((HOST, PORT))
        print("TCP server started on port: ", PORT)

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_socket.bind((HOST, PORT))
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("UDP server started on port: ", PORT)
        
        tcp_socket.listen(5)
        print("Server is listening...")

        threading.Thread(target=handle_udp_connection, args=(udp_socket,), daemon=True).start()
        
        while True:
            client, addr = tcp_socket.accept()
            print(f'Connected to client: {addr}')
            try:
                get_nickname_from_client(client)
            except ConnectionResetError:
                print("Client suddenly disconnected!")
                continue
            
            thread = threading.Thread(target=handle_tcp_connection, args=(client,), daemon=True)
            threads.append(thread)
            thread.start()
            
    except KeyboardInterrupt:
        exit()


def handle_tcp_connection(client):
    while True:
        try:
            message = client.recv(1024).decode("ascii")
            sender, recipient, message_content = split_message(message)
            print(sender, recipient, message_content)

            recipient_index = nicknames.index(recipient)
            destination_client = clients[recipient_index]
            destination_client.send(f"{sender}: {message_content}".encode("ascii"))

        except ConnectionError:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            print(f"{nickname} disconnected!")
            nicknames.remove(nickname)
            break
        except MissingSenderError:
            print("No sender given!")
            client.send("No sender given!".encode("ascii"))
            continue
        except MissingRecipientError:
            print("No recipient given!")
            client.send("No recipient given!".encode("ascii"))
            continue
        except ValueError:
            print("Recipient not found!")
            client.send("Recipient not found!".encode("ascii"))
            continue
        except (KeyboardInterrupt, EOFError):
            exit()


def handle_udp_connection(udp_socket):
    while True:
        try:
            message, addr = udp_socket.recvfrom(1024)
        except OSError:
            return
        
        message = message.decode("ascii")
        print(f"<udp> Received message from {addr}: {message}")
        for client in clients:
            client_addr = client.getpeername()
            nickname = nicknames[clients.index(client)]
            if client_addr != addr:
                print("received udp, try to send udp stuff to the rest")
                udp_socket.sendto(f"{nickname}: {message}".encode("ascii"), client_addr)


def get_nickname_from_client(client):
    nickname = client.recv(1024).decode("ascii")
    
    while len(nickname) <= 2 or nickname in nicknames:
        if len(nickname) <= 2:
            client.send("Nickname must be longer than 2 letters.".encode("ascii"))
        else:
            client.send("Nickname is already taken.".encode("ascii"))
        nickname = client.recv(1024).decode("ascii")
        
    nicknames.append(nickname)
    clients.append(client)
    print(f"Nickname is {nickname}")
    client.send("OK".encode("ascii"))
    
    
def split_message(message):
    try:
        colon_pos = message.index(":")
    except ValueError  as exc:
        raise MissingSenderError("No sender given!") from exc

    try:
        at_pos = message.index("@")
    except ValueError as exc:
        raise MissingRecipientError("No recipient given!") from exc

    # Extract the sender, recipient, and message strings
    sender = message[:colon_pos].strip()
    recipient = message[at_pos + 1 :].split()[0]
    message = message[at_pos + 1 + len(recipient) + 1 :].strip()

    return sender, recipient, message


class MissingSenderError(Exception):
    def __init__(self, message):
        self.message = message


class MissingRecipientError(Exception):
    def __init__(self, message):
        self.message = message


class UdpError(Exception):
    def __init__(self, message):
        self.message = message


if __name__ == "__main__":
    main()
