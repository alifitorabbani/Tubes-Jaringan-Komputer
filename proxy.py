import socket
import threading
import os

HOST = '172.20.10.4'
PROXY_PORT = 8080
WEB_SERVER_HOST = '192.168.18.49'
WEB_SERVER_PORT = 8000
BUFFER_SIZE = 1024
CACHE_DIR = './cache'

os.makedirs(CACHE_DIR, exist_ok=True)
cache_lock = threading.Lock()

# --- Cache Functions ---
def get_cached(path):
    file_path = os.path.join(CACHE_DIR, path.strip('/').replace('/', '_'))
    with cache_lock:
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                return f.read()
    return None

def save_cache(path, data):
    file_path = os.path.join(CACHE_DIR, path.strip('/').replace('/', '_'))
    with cache_lock:
        with open(file_path, 'wb') as f:
            f.write(data)

# --- Handle Client ---
def handle_client(client_socket, addr):
    thread_name = threading.current_thread().name
    try:
        request = client_socket.recv(BUFFER_SIZE).decode()
        request_line = request.splitlines()[0] if request.splitlines() else "EMPTY REQUEST"
        print(f"[Proxy][{thread_name}] Request from {addr}: {request_line}")

        try:
            path = request.split(' ')[1]
            if path == '/':
                path = '/index.html'
        except IndexError:
            path = '/index.html'

        cached_data = get_cached(path)
        if cached_data:
            print(f"[Cache HIT] {path}")
            client_socket.sendall(b"HTTP/1.1 200 OK\r\n\r\n" + cached_data)
        else:
            print(f"[Cache MISS] {path} -> Forwarding")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
                    server_sock.settimeout(3)
                    server_sock.connect((WEB_SERVER_HOST, WEB_SERVER_PORT))
                    server_sock.sendall(request.encode())

                    response = b''
                    while True:
                        chunk = server_sock.recv(BUFFER_SIZE)
                        if not chunk:
                            break
                        response += chunk

                client_socket.sendall(response)
                if b"\r\n\r\n" in response:
                    save_cache(path, response.split(b'\r\n\r\n',1)[1])

            except socket.timeout:
                print(f"[Proxy] 504 Gateway Timeout for {path}")
                client_socket.sendall(
                    b"HTTP/1.1 504 Gateway Timeout\r\nContent-Type: text/html\r\n\r\n"
                    b"<h1>504 Gateway Timeout</h1>"
                )
            except Exception as e:
                print(f"[Proxy] 502 Bad Gateway for {path}: {e}")
                client_socket.sendall(
                    b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/html\r\n\r\n"
                    b"<h1>502 Bad Gateway</h1>"
                )

    except Exception as e:
        print(f"[Proxy] Error: {e}")
    finally:
        client_socket.close()

# --- Start Proxy Server ---
def start_proxy():
    print("=== Proxy Server Menu ===")
    print("1. Single-threaded")
    print("2. Multi-threaded")
    while True:
        try:
            choice = int(input("Pilih mode (1/2): "))
            if choice in [1,2]:
                break
        except ValueError:
            pass
        print("Input tidak valid. Pilih 1 atau 2.")

    proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_sock.bind((HOST, PROXY_PORT))
    proxy_sock.listen(5)
    mode = "Single-threaded" if choice == 1 else "Multi-threaded"
    print(f"[Proxy] {mode} Listening on {HOST}:{PROXY_PORT}")

    while True:
        client, addr = proxy_sock.accept()
        if choice == 1:
            handle_client(client, addr)
        else:
            thread = threading.Thread(target=handle_client, args=(client, addr))
            thread.start()

if __name__ == "__main__":
    start_proxy()