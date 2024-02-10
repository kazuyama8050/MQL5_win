import socket 

class SocketHandler():
    def __init__(self, host, port):
        self._host = host
        self._port = port
        server_socket, client_socket, client_address = self.create_socket()
        self._server_socket = server_socket
        self._client_socket = client_socket
        self._client_address = client_address
        
    def create_socket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self._host, self._port))
        server_socket.listen(1)  # 1つの接続まで待ち受け
        client_socket, client_address = server_socket.accept()
        return server_socket, client_socket, client_address
    
    def recv(self):
        return self._client_socket.recv(1024).decode('utf-8')
        
    def is_recv_force_stop_cmd(self):
        return self.recv() == "force_stop"
    
    def close(self):
        self._client_socket.close()
        self._server_socket.close()