from asyncio import sleep
import socket
import threading
import select
import time

HOST = "localhost"
PORT = 7878

tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
tcp_client.connect((HOST, PORT))

udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
udp_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udp_client.bind(("", tcp_client.getsockname()[1]))
udp_client.connect((HOST, PORT))


terminal_lock = threading.Lock()


while True:
    nickname = input("Choose your nickname (must be longer than 2 letters): ")
    tcp_client.send("{}".format(nickname).encode("ascii"))

    response = tcp_client.recv(1024).decode("ascii")
    if response.startswith("OK"):
        break
    else:
        print(response)


def receive():
    while True:
        ready_clients, _, _ = select.select([tcp_client, udp_client], [], [])

        if udp_client in ready_clients:
            try:
                message, addr = udp_client.recvfrom(1024)
                with terminal_lock:
                    print("<udp> ", message.decode("ascii"))
            except ConnectionResetError:
                with terminal_lock:
                    print("<udp> An ConnectionResetError error occured!")
                udp_client.close()
                break

        elif tcp_client in ready_clients:
            try:
                message = tcp_client.recv(1024).decode("ascii")
                with terminal_lock:
                    print("<tcp> ", message)
            except ConnectionResetError:
                with terminal_lock:
                    print("<tcp> An ConnectionResetError error occured!")
                tcp_client.close()
                break


def write():
    print("Write your messages in given formats: \n tcp: @to message, \n udp: starts with u command")

    while True:
        with terminal_lock:
            client_input = input(">")

        if not client_input:
            continue
        elif client_input.lower().startswith("u"):
            udp_client.sendto(client_input[1:].encode("ascii"), (HOST, PORT))
        else:
            message = "{}: {}".format(nickname, client_input)
            tcp_client.send(message.encode("ascii"))
            
        # Pause the thread to give the terminal to the receive function
        time.sleep(0.1)

try:
    write_thread = threading.Thread(target=write, daemon=True)
    write_thread.start()
    receive()
except (KeyboardInterrupt, EOFError):
    exit()
