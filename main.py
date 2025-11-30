import socket
import threading
import time
from datetime import datetime
import sys


class Client: 
    def __init__(self, host = "0.0.0.0", port = 10000):
        self.host = host
        self.port = port
        self.clients = []
        self.players = {}
        self.running = True
        self.lock = threading.Lock()

        
    def start(self):
        print("players can connect: forcedentry.onrender.com")
        print(f"server running on {self.host}:{self.port}")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1.0)

        try: 
            self.socket.bind((self.host, self.port))
            self.socket.listen()

            print(f"server running on {self.host}:{self.port}")
            print("waiting for unity clients..")

            while self.running:
                try:
                    client_socket, client_address = self.socket.accept()
                    print(f" client connected : {client_address}")
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )

                    client_thread.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"accept error: " + e)
                    break
        except Exception as e:
            print(f"server error" + e)

        finally:
            self.stop()


    def handle_client(self, client_socket, client_address):
        client_id = f"{client_address[0]}:{client_address[1]}"

        try:
            client_socket.settimeout(1.0)

            welcome_msg = f"your id {client_id}"
            client_socket.sendall(welcome_msg.encode('utf-8'))
            print(f"sent to {client_address}")

            with self.lock:
                self.clients.append(client_socket)
                self.players[client_id] = {
                    'socket': client_socket,
                    'address': client_address,
                    'username': f'player{len(self.players)}',
                    'position': '0,0,0'
                }

            self.broadcast(f"player_joined:{client_id},Player{len(self.players)}", client_id)

            buffer = ""
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break

                    buffer += data.decode('utf-8')

                    while '\n' in buffer:
                        message, buffer = buffer.split('\n', 1)
                        message = message.strip()

                        if message: 
                            self.process_message(client_id, message)
                        

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"client error: " + e)

        except Exception as e:
            print(f"client handler error: {client_address}" + e)

        finally: 
            with self.lock:
                if client_socket in self.clients:
                    self.clients_remove(client_socket)
                if client_id in self.players:
                    del self.players[client_id]

            try: 
                client_socket.close()
            except: 
                pass

            print(f" client disconnected: {client_address}")
            self.broadcast(f"player_left:{client_id}", "")

    def process_message(self, client_id, message):
        print(f"from {client_id}: {message}")

        try: 
            if ':' in message:
                command, data = message.split(':', 1)

                if command == "join":
                    with self.lock:
                        if client_id in self.players:
                            self.players[client_id]['username'] = data

                        print(f"player {client_id} set username: "+data)

                        self.broadcast(f"lobby_info:Player {data} joined", client_id)


                elif command == "position":
                    with self.lock:
                        if client_id in self.players:
                            self.players[client_id]['position'] = data
                        
                    self.broadcast(f"player_position:{client_id},{data}", client_id)


                elif command == "shoot":
                    self.broadcast(f"shoot:{client_id},{data}", client_id) 
                    print(f"player {client_id} shot: {data}")


                elif command == "ping":
                    with self.lock:
                        if client_id in self.players:
                            self.players[client_id]['socket'].sendall(b"pong: \n")

        except Exception as e:
            print(f"message processing error: " + e)

    

    def broadcast(self, message, exclude_client_id):
        with self.lock:
            for client_id, player in self.players.items():
                if client_id != exclude_client_id:
                    try:
                        player['socket'].sendall(f"{message}\n".encode('utf-8'))
                    except Exception as e:
                        print(f"broadcast error to {client_id}: " + e)


    def stop(self):
        print("stopping server..")
        self.running = False

        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
        try:
            self.socket.close()
        except:
            pass
        print("server stopped")



if __name__ == "__main__":
    server = Client(port=10000)
    try:
        server.start()
    except KeyboardInterrupt:
        print(f"server stopped by user")
    except Exception as e:
        print(f"server crashed" + e)

        import traceback
        traceback.print_exc()
                        




