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

        udp_thread = threading.Thread(target=handle_udp_connection, args=(udp_socket,), daemon=True).start()
        
        while True:
            client, addr = tcp_socket.accept()
            print("Connected to client: {}".format(addr))
            
            try:
                client.send("NICK".encode("ascii"))
                nickname = client.recv(1024).decode("ascii")
                if len(nickname) < 2:
                    client.send("Nickname is too short!".encode("ascii"))
                    nickname = client.recv(1024).decode("ascii")
                nicknames.append(nickname)
                clients.append(client)

                print("Nickname is {}".format(nickname))
                client.send(
                    "You have been added to server with nickname {}!".format(
                        nickname
                    ).encode("ascii")
                )
                
            except ConnectionResetError:
                print("Client suddenly disconnected!")
                continue
            
            thread = threading.Thread(target=handle_tcp_connection, args=(client,))
            threads.append(thread)
            thread.start()
            
    except KeyboardInterrupt:
        for t in threads:
            t.join()
        udp_socket.close()
        tcp_socket.close()
        udp_thread.join()
        exit()


def handle_tcp_connection(client):
    while True:
        try:
            message = client.recv(1024).decode("ascii")
            sender, recipient, message_content = split_message(message)
            print(sender, recipient, message_content)

            if not recipient:
                client.send("No recipient given!".encode("ascii"))
            else:
                recipient_index = nicknames.index(recipient)
                destination_client = clients[recipient_index]
                destination_client.send(
                    "{}: {}".format(sender, message_content).encode("ascii"))

        except ConnectionError:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            print("{} disconnected!".format(nickname))
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


def handle_udp_connection(udp_socket):
    while True:
        message, addr = udp_socket.recvfrom(1024)
        print("<udp> Received message from {}: {}".format(addr, message.decode("ascii")))
        for client in clients:
            client_addr = client.getpeername()
            nickname = nicknames[clients.index(client)]
            if client_addr != addr:
                print("received udp, try to send udp stuff to the rest")
                udp_socket.sendto("{}: {}".format(nickname, message.decode("ascii")).encode("ascii"), client_addr)



def split_message(message):
    try:
        colon_pos = message.index(":")
    except ValueError:
        raise MissingSenderError("No sender given!")

    try:
        at_pos = message.index("@")
    except ValueError:
        raise MissingRecipientError("No recipient given!")

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
