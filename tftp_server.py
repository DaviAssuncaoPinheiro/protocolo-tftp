import socket
import os
import struct

# Constantes TFTP
OPCODE_RRQ = 1  # Read Request
OPCODE_WRQ = 2  # Write Request
OPCODE_DATA = 3  # Data Packet
OPCODE_ACK = 4  # Acknowledgment
OPCODE_ERROR = 5  # Error Packet
BLOCK_SIZE = 512  # Tamanho do bloco de dados

def send_error(socket, addr, error_code, error_msg):
    error_packet = struct.pack('!H', OPCODE_ERROR) + struct.pack('!H', error_code) + error_msg.encode() + b'\0'
    socket.sendto(error_packet, addr)

def handle_request(data, server_socket, addr):
    opcode = struct.unpack('!H', data[:2])[0]
    
    if opcode == OPCODE_RRQ:  # Read Request
        filename = data[2:-1].decode()
        if os.path.isfile(filename):
            send_file(filename, server_socket, addr)
        else:
            send_error(server_socket, addr, 1, "File not found")
    
    elif opcode == OPCODE_WRQ:  # Write Request
        filename = data[2:-1].decode()
        receive_file(filename, server_socket, addr)

def send_file(filename, server_socket, addr):
    block_num = 1
    with open(filename, 'rb') as f:
        while True:
            data = f.read(BLOCK_SIZE)
            if not data:
                break
            data_packet = struct.pack('!HH', OPCODE_DATA, block_num) + data
            server_socket.sendto(data_packet, addr)
            # Esperar ACK
            ack, _ = server_socket.recvfrom(1024)
            ack_block_num = struct.unpack('!H', ack[2:4])[0]
            if ack_block_num != block_num:
                print("ACK block number mismatch")
                break
            block_num += 1
    # Enviar último ACK
    server_socket.sendto(struct.pack('!HH', OPCODE_DATA, block_num), addr)

def receive_file(filename, server_socket, addr):
    block_num = 0
    with open(filename, 'wb') as f:
        while True:
            data, _ = server_socket.recvfrom(1024)
            opcode = struct.unpack('!H', data[:2])[0]
            if opcode == OPCODE_DATA:
                block_num += 1
                f.write(data[4:])  # Escrever dados no arquivo
                # Enviar ACK
                ack_packet = struct.pack('!HH', OPCODE_ACK, block_num)
                server_socket.sendto(ack_packet, addr)
                if len(data) < BLOCK_SIZE + 4:  # Último pacote
                    break
            elif opcode == OPCODE_ERROR:
                print("Received error from client")
                break

def start_tftp_server(port=69):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', port))
    print(f'Servidor TFTP iniciado na porta {port}')

    while True:
        data, addr = server_socket.recvfrom(1024)
        handle_request(data, server_socket, addr)

if __name__ == "__main__":
    start_tftp_server()