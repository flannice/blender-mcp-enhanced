# Level 3: Full Blender MCP Test
# Run this in Blender: Scripting workspace -> Text Editor -> New -> Paste -> Run Script

import socket
import json
import sys
import time

HOST = '127.0.0.1'
PORT = 9876
TIMEOUT = 180  # 3 minutes for Blender startup

print("=" * 50)
print("Level 3: Full Blender MCP Test")
print("=" * 50)

def test_mcp():
    try:
        print("[1] Creating socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        print("    OK")

        print("[2] Connecting to server...")
        sock.connect((HOST, PORT))
        print("    OK - Connected!")

        print("[3] Waiting for server welcome...")
        welcome = sock.recv(4096)
        print(f"    Welcome: {welcome}")
        print("    OK - Server is ready!")

        print("[4] Sending ping command...")
        sock.settimeout(60)  # Shorter timeout after connection
        command = {"tool": "ping", "params": {}}
        sock.sendall(json.dumps(command).encode('utf-8'))
        print("    OK - Sent")

        print("[5] Waiting for response...")
        response = b''
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                print(f"    Received {len(chunk)} bytes")
                break  # Get first chunk only
        except socket.timeout:
            print("    TIMEOUT - No response after 60s")
            sock.close()
            return False

        print("[6] Parsing response...")
        sock.close()

        if response:
            result = json.loads(response.decode('utf-8'))
            print(f"    Response: {result}")
            print()
            print("=" * 50)
            if result.get("status") == "ok":
                print("SUCCESS: MCP is working!")
                return True
            else:
                print("ERROR:", result.get("message"))
                return False
        else:
            print("FAILED: Empty response")
            return False

    except ConnectionRefusedError:
        print("FAILED: Connection refused")
        print("Is the server running?")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mcp()
    print("=" * 50)
    sys.exit(0 if success else 1)