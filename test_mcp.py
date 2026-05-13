"""
Blender MCP Simple Connection Test
Run this in Blender Scripting workspace (Text Editor -> Run Script)
"""

import socket
import json

HOST = '127.0.0.1'
PORT = 9876
TIMEOUT = 30

def test():
    print("=" * 50)
    print("MCP Connection Test")
    print("=" * 50)
    print(f"Target: {HOST}:{PORT}")
    print(f"Timeout: {TIMEOUT}s")
    print()

    try:
        print("[1] Creating socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        print("    OK")

        print("[2] Connecting to server...")
        sock.connect((HOST, PORT))
        print("    OK - Connected!")

        print("[3] Sending check_connection...")
        cmd = json.dumps({"tool": "check_connection", "params": {}})
        sock.sendall(cmd.encode('utf-8'))
        print("    OK - Sent!")

        print("[4] Waiting for response...")
        data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
            print(f"    Received {len(chunk)} bytes...")
            if len(data) > 4096:
                break

        sock.close()

        print("[5] Parsing response...")
        result = json.loads(data.decode('utf-8'))
        print()
        print("=" * 50)
        print("RESULT:")
        print(f"  Status: {result.get('status')}")
        print(f"  Message: {result.get('message')}")
        print("=" * 50)

        if result.get('status') == 'ok':
            print("\n[SUCCESS] Connection working!")
            return True
        else:
            print("\n[FAILED] Server returned error")
            return False

    except socket.timeout:
        print("    TIMEOUT - Server not responding")
        print("\n[FAILED] Connection timeout")
        print("Make sure server.py is running and listening on port 9876")
        return False

    except ConnectionRefusedError:
        print("    REFUSED - Server not running")
        print("\n[FAILED] Connection refused")
        print("Run 'python server.py' first")
        return False

    except json.JSONDecodeError as e:
        print(f"    JSON Error: {e}")
        print(f"    Raw data: {data[:200] if data else 'empty'}")
        print("\n[FAILED] Invalid response from server")
        return False

    except Exception as e:
        print(f"    ERROR: {e}")
        print("\n[FAILED] Unexpected error")
        return False

if __name__ == "__main__":
    test()