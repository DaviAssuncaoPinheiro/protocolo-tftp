import argparse
import os
import socket

from tftp_packet import (
    parse_packet,
    build_data,
    build_ack,
    build_error,
    DATA,
    ACK,
    RRQ,
    WRQ,
    MAX_DATA_SIZE,
)


def send_file(sock, addr, filename):
    filepath = os.path.abspath(filename)

    if not os.path.exists(filepath):
        print("Arquivo não encontrado:", filepath)
        sock.sendto(build_error(1), addr)
        return

    print("\n[DOWNLOAD]")
    print("Arquivo:", filepath)
    print("Tamanho:", os.path.getsize(filepath), "bytes")

    block = 1

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(MAX_DATA_SIZE)

            sock.sendto(build_data(block, chunk), addr)
            print(f"Enviado bloco {block} ({len(chunk)} bytes)")

            try:
                ack_data, _ = sock.recvfrom(1024)
            except socket.timeout:
                print("Timeout esperando ACK")
                return

            ack = parse_packet(ack_data)

            if ack["opcode"] != ACK or ack["block_number"] != block:
                print("Erro no ACK")
                return

            if len(chunk) < MAX_DATA_SIZE:
                print("Fim do envio")
                break

            block += 1


def receive_file(sock, addr, filename):
    filepath = os.path.abspath(filename)

    print("\n[UPLOAD]")
    print("Salvando em:", filepath)

    # ACK inicial obrigatório
    sock.sendto(build_ack(0), addr)

    expected_block = 1

    with open(filepath, "wb") as f:
        while True:
            try:
                data_packet, _ = sock.recvfrom(1024)
            except socket.timeout:
                print("Timeout recebendo dados")
                return

            packet = parse_packet(data_packet)

            if packet["opcode"] != DATA:
                print("Pacote inválido")
                return

            if packet["block_number"] != expected_block:
                print("Bloco fora de ordem")
                return

            f.write(packet["data"])

            print(f"Recebido bloco {expected_block} ({len(packet['data'])} bytes)")

            sock.sendto(build_ack(expected_block), addr)

            if len(packet["data"]) < MAX_DATA_SIZE:
                print("Fim do recebimento")
                break

            expected_block += 1


def handle_request(data, addr):
    packet = parse_packet(data)

    print("\nNova requisição:", packet)

    # socket dedicado (porta dinâmica TFTP)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 0))
    sock.settimeout(5)

    print("Usando porta:", sock.getsockname())

    if packet["opcode"] == RRQ:
        send_file(sock, addr, packet["filename"])

    elif packet["opcode"] == WRQ:
        receive_file(sock, addr, packet["filename"])


def start_server(host="0.0.0.0", port=6969):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))

    print(f"TFTP Server rodando em {host}:{port}")

    while True:
        data, addr = server.recvfrom(1024)
        handle_request(data, addr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TFTP Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=6969)

    args = parser.parse_args()

    start_server(args.host, args.port)