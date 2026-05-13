# Level 2: Blender Socket Test
# Run this in Blender: Scripting workspace -> Python Console
# Paste each line and press Enter

import socket
import json
import sys

print("=" * 40)
print("Level 2: Blender Socket Test")
print("=" * 40)

# Step 1: Create socket
print("[1] Creating socket...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("    OK")

# Step 2: Connect
print("[2] Connecting to 127.0.0.1:9876...")
sock.settimeout(10)
try:
    sock.connect(('127.0.0.1', 9876))
    print("    OK - Connected!")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

# Step 3: Send ping
print("[3] Sending ping...")
sock.settimeout(30)
command = {"tool": "ping", "params": {}}
sock.sendall(json.dumps(command).encode('utf-8'))
print("    OK - Sent")

# Step 4: Wait for response
print("[4] Waiting for response...")
response = b''
try:
    chunk = sock.recv(4096)
    response += chunk
    print(f"    OK - Received {len(chunk)} bytes")
except socket.timeout:
    print("    TIMEOUT - No response from server")
except Exception as e:
    print(f"    ERROR: {e}")

# Step 5: Parse and display
print("[5] Parsing response...")
sock.close()

if response:
    try:
        result = json.loads(response.decode('utf-8'))
        print(f"    Response: {result}")
        print()
        if result.get("status") == "ok":
            print("SUCCESS: Connection working!")
        else:
            print("Server returned error:", result.get("message"))
    except Exception as e:
        print(f"    Parse error: {e}")
        print(f"    Raw: {response[:200]}")
else:
    print("    No response received")
    print("    Possible cause: Server received data but didn't respond")

print("=" * 40)