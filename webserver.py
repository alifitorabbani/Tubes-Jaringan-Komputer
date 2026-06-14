import socket
import threading
import os

HOST = '0.0.0.0'
TCP_PORT = 8000
UDP_PORT = 9000
BUFFER_SIZE = 1024
WEB_DIR = './www'

# --- Handle TCP Client ---
def handle_tcp_client(client_socket, address):
    thread_name = threading.current_thread().name
    try:
        request = client_socket.recv(BUFFER_SIZE).decode()
        request_line = request.splitlines()[0] if request.splitlines() else "EMPTY REQUEST"
        print(f"[TCP][{thread_name}] Request from {address}: {request_line}")

        try:
            path = request.split(' ')[1]
            if path == '/':
                path = '/index.html'
        except IndexError:
            path = '/index.html'

        file_path = os.path.join(WEB_DIR, path.strip('/'))
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                response_body = f.read()
            response_header = b"HTTP/1.1 200 OK\r\n\r\n"
        else:
            response_header = b"HTTP/1.1 404 Not Found\r\n\r\n"
            response_body = b"<h1>404 Not Found</h1>"

        client_socket.sendall(response_header + response_body)

    except Exception as e:
        print(f"[TCP][{thread_name}] Error: {e}")
    finally:
        client_socket.close()

# --- Handle UDP ---
def handle_udp():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, UDP_PORT))
    print(f"[UDP] Listening on {HOST}:{UDP_PORT}")

    while True:
        data, addr = udp_sock.recvfrom(BUFFER_SIZE)
        print(f"[UDP] Received {data} from {addr}")
        udp_sock.sendto(data, addr)  # echo balik

# --- Start TCP Server ---
def start_tcp_server():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind((HOST, TCP_PORT))
    tcp_sock.listen(5)
    print(f"[TCP] Listening on {HOST}:{TCP_PORT}")

    while True:
        client, addr = tcp_sock.accept()
        thread = threading.Thread(target=handle_tcp_client, args=(client, addr))
        thread.start()
        print(f"[TCP] Spawn thread {thread.name} for {addr}")

# --- Main ---
if __name__ == "__main__":
    threading.Thread(target=handle_udp, daemon=True).start()
    start_tcp_server()