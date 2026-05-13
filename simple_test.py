# Simple test - paste this in Blender Python Console
import socket, json

sock = socket.socket()
sock.settimeout(30)
sock.connect(('127.0.0.1', 9876))

# Read welcome
print(sock.recv(4096).decode())

# Send ping
sock.sendall(json.dumps({"tool": "ping", "params": {}}).encode())
print(sock.recv(4096).decode())

sock.close()
print("Test complete!")