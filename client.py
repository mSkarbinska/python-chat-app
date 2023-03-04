import socket
import threading
import select

HOST = "localhost"
PORT = 7878

nickname = input("Choose your nickname: ")

tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
tcp_client.connect((HOST, PORT))

udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_client.bind(("", tcp_client.getsockname()[1]))
udp_client.connect((HOST, PORT))


def receive():
    while True:
        ready_clients, _, _ = select.select([tcp_client, udp_client], [], [])

        if udp_client in ready_clients:
            try:
                message, addr = udp_client.recvfrom(1024)
                print("<udp> ", message.decode("ascii"))
            except ConnectionResetError:
                print("<udp> An ConnectionResetError error occured!")
                udp_client.close()
                break

        elif tcp_client in ready_clients:
            try:
                message = tcp_client.recv(1024).decode("ascii")
                if message == "NICK":
                    tcp_client.send(nickname.encode("ascii"))
                else:
                    print("<tcp> ", message)
            except ConnectionResetError:
                print("<tcp> An ConnectionResetError error occured!")
                tcp_client.close()
                break


def write():
    while True:
        try:
            print("Write your message (tcp format: @to message, udp - starts with u command): ")
            client_input = input(">")
        except Exception:
            print("saa")
            exit()
        if not client_input:
            continue
        elif client_input == "exit":
            print("Exiting...")
            write_thread.join()
            exit(0)
            break
        elif client_input.lower().startswith("u"):
            udp_client.sendto(client_input[1:].encode("ascii"), (HOST, PORT))
        else:
            message = "{}: {}".format(nickname, client_input)
            tcp_client.send(message.encode("ascii"))


try:
    write_thread = threading.Thread(target=write, daemon=True)
    write_thread.start()
    receive()
except (KeyboardInterrupt, EOFError):
    write_thread.close()
    exit()
