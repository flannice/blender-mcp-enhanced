# Blender MCP Connection Test Script
# Run this in Blender Scripting workspace to test connection

import socket
import json
import sys

def test_mcp_connection():
    HOST = '127.0.0.1'
    PORT = 9876

    print("=" * 50)
    print("Blender MCP Connection Test")
    print("=" * 50)
    print(f"Target: {HOST}:{PORT}")
    print()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)

    try:
        print("[1/3] Connecting to MCP server...")
        sock.connect((HOST, PORT))
        print("    OK - Connected")

        print("[2/3] Sending check_connection command...")
        command = {"tool": "check_connection", "params": {}}
        sock.sendall(json.dumps(command).encode('utf-8'))
        print("    OK - Command sent")

        print("[3/3] Waiting for response...")
        response = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if len(response) > 8192:
                break

        result = json.loads(response.decode('utf-8'))
        print("    OK - Response received")
        print()
        print("=" * 50)
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Message: {result.get('message', 'no message')}")
        print("=" * 50)

        sock.close()

        if result.get("status") == "ok":
            print("\nRESULT: Connection SUCCESS")
            return True
        else:
            print("\nRESULT: Connection FAILED")
            return False

    except socket.timeout:
        print("    TIMEOUT - Server did not respond within 10s")
        print("\nRESULT: Connection FAILED - Timeout")
        return False

    except ConnectionRefusedError:
        print("    REFUSED - Server not running on port 9876")
        print("\nRESULT: Connection FAILED - Server not running")
        print("Solution: Run 'python server.py' in blender-mcp-enhanced folder")
        return False

    except Exception as e:
        print(f"    ERROR: {e}")
        print("\nRESULT: Connection FAILED")
        return False

    finally:
        sock.close()

if __name__ == "__main__":
    success = test_mcp_connection()
    sys.exit(0 if success else 1)