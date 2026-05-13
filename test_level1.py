# Level 1: Pure Python Echo Test (no Blender needed)
# Save this as test_level1.py and run: python test_level1.py

import socket
import json
import sys

HOST = '127.0.0.1'
PORT = 9876

print("=" * 50)
print("Level 1: Pure Socket Echo Test")
print("=" * 50)

try:
    print("[1] Creating socket...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    print("    OK")

    print("[2] Connecting to server...")
    sock.connect((HOST, PORT))
    print("    OK - Connected!")

    print("[3] Sending echo test...")
    test_data = {"tool": "ping", "params": {}}
    sock.sendall(json.dumps(test_data).encode('utf-8'))
    print("    OK - Sent:", test_data)

    print("[4] Waiting for response...")
    sock.settimeout(30)

    response = b''
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            print(f"    Received {len(chunk)} bytes")
            break  # Don't wait for more
        except socket.timeout:
            print("    Timeout waiting for data")
            break

    sock.close()

    print("[5] Parsing response...")
    if response:
        result = json.loads(response.decode('utf-8'))
        print("    Response:", result)
        print()
        print("=" * 50)
        print("RESULT: SUCCESS - Server is working!")
        print("=" * 50)
    else:
        print("    No response received")

except ConnectionRefusedError:
    print("    FAILED: Server not running")
    print("    Run 'python server.py' first")
except socket.timeout:
    print("    FAILED: Connection timeout")
    print("    Server may be stuck or not receiving data")
except Exception as e:
    print(f"    FAILED: {e}")

print()
input("Press Enter to exit...")