import socket
import time
import threading
import os
import csv

PROXY_HOST = '172.20.10.4'
PROXY_PORT = 8080
UDP_HOST = '192.168.18.49'
UDP_PORT = 9000
BUFFER_SIZE = 1024
UDP_COUNT = 10

CSV_FILE = "qos_results.csv"
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario","rtt_min_ms","rtt_avg_ms","rtt_max_ms","jitter_avg_ms","packet_loss_percent"])

# --- HTTP Request via Proxy ---
def http_request(path="/index.html"):
    try:
        start = time.time()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((PROXY_HOST, PROXY_PORT))
            request = f"GET {path} HTTP/1.1\r\nHost: {PROXY_HOST}\r\n\r\n"
            s.sendall(request.encode())
            response = b''
            while True:
                chunk = s.recv(BUFFER_SIZE)
                if not chunk:
                    break
                response += chunk
        end = time.time()
        elapsed_ms = (end - start) * 1000
        print(f"[HTTP] {path} -> {len(response)} bytes, {elapsed_ms:.2f} ms")
        return elapsed_ms
    except Exception as e:
        print(f"[HTTP] Error: {e}")
        return None

# --- UDP QoS Test ---
def udp_test(scenario="idle"):
    rtts = []
    lost = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(1)
        for i in range(UDP_COUNT):
            timestamp = time.time()
            msg = f"Ping {i} {timestamp}".encode()
            try:
                s.sendto(msg, (UDP_HOST, UDP_PORT))
                start = time.time()
                data, addr = s.recvfrom(BUFFER_SIZE)
                end = time.time()
                rtt = (end - start) * 1000
                rtts.append(rtt)
                print(f"[UDP] {i} → RTT: {rtt:.2f} ms, {data.decode()}")
            except socket.timeout:
                print(f"[UDP] {i} → Timeout")
                lost += 1

    if rtts:
        rtt_min = min(rtts)
        rtt_avg = sum(rtts)/len(rtts)
        rtt_max = max(rtts)
        jitters = [abs(rtts[i]-rtts[i-1]) for i in range(1,len(rtts))]
        jitter_avg = sum(jitters)/len(jitters) if jitters else 0
    else:
        rtt_min = rtt_avg = rtt_max = jitter_avg = 0

    packet_loss = (lost/UDP_COUNT)*100
    print(f"RTT min/avg/max: {rtt_min:.2f}/{rtt_avg:.2f}/{rtt_max:.2f} ms")
    print(f"Jitter avg: {jitter_avg:.2f} ms")
    print(f"Packet Loss: {lost}/{UDP_COUNT} ({packet_loss:.2f}%)")

    # Simpan ke CSV
    with open(CSV_FILE,"a",newline="") as f:
        writer = csv.writer(f)
        writer.writerow([scenario,rtt_min,rtt_avg,rtt_max,jitter_avg,packet_loss])

# --- Multi-client Simulation ---
def multi_client_simulation(client_count=5):
    threads = []
    for i in range(client_count):
        t = threading.Thread(target=http_request,args=("/index.html",))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

# --- Main ---
if __name__ == "__main__":
    print("=== HTTP Test via Proxy ===")
    http_request("/index.html")
    http_request("/osi.html")
    http_request("/tcpip.html")
    http_request("/qos.html")
    http_request("/implementation.html")

    print("\n=== UDP QoS Test ===")
    udp_test(scenario="idle")

    print("\n=== Multi-Client Simulation (HTTP) ===")
    multi_client_simulation(client_count=5)