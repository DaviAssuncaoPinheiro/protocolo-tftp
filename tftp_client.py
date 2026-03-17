import socket
import argparse
import os

from tftp_packet import (
    build_rrq,
    build_wrq,
    build_ack,
    build_data,
    parse_packet,
    DATA,
    ACK,
    MAX_DATA_SIZE,
)


def download(server_ip, port, remote_filename, local_filename):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    sock.sendto(build_rrq(remote_filename), (server_ip, port))
    expected_block = 1

    with open(local_filename, "wb") as f:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                print("Timeout no download")
                return

            packet = parse_packet(data)

            if packet["opcode"] != DATA:
                continue

            if packet["block_number"] != expected_block:
                continue

            print(f" Bloco {expected_block} ({len(packet['data'])} bytes)")

            f.write(packet["data"])
            sock.sendto(build_ack(expected_block), addr)

            if len(packet["data"]) < MAX_DATA_SIZE:
                break

            expected_block += 1

    print(" Download concluído\n")

def upload(server_ip, port, filename):
    if not os.path.isfile(filename):
        print("Arquivo não encontrado")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    sock.sendto(build_wrq(filename), (server_ip, port))

    try:
        data, addr = sock.recvfrom(1024)
    except socket.timeout:
        print("Timeout aguardando ACK")
        return

    packet = parse_packet(data)

    if packet["opcode"] != ACK:
        print("Erro no ACK inicial")
        return

    block = 1

    with open(filename, "rb") as f:
        while True:
            chunk = f.read(MAX_DATA_SIZE)

            sock.sendto(build_data(block, chunk), addr)
            print(f"Bloco {block} ({len(chunk)} bytes)")

            try:
                ack_data, _ = sock.recvfrom(1024)
            except socket.timeout:
                print("Timeout aguardando ACK")
                return

            ack = parse_packet(ack_data)

            if ack["block_number"] != block:
                print("ACK incorreto")
                return

            if len(chunk) < MAX_DATA_SIZE:
                break

            block += 1

    print("Upload concluído\n")


def cli():
    print("=" * 40)
    print("TFTP CLIENT")
    print("=" * 40)

    server_ip = input("IP do servidor: ").strip()
    port_input = input("Porta (default 6969): ").strip()
    port = int(port_input) if port_input else 6969

    while True:
        print("\nEscolha uma opção:")
        print("1 - Download arquivo")
        print("2 - Upload arquivo")
        print("3 - Sair")

        choice = input("Opção: ").strip()

        if choice == "1":
            remote = input(" Nome do arquivo no servidor: ").strip()
            local = input(" Nome local (enter = mesmo nome): ").strip()

            if not local:
                local = remote

            download(server_ip, port, remote, local)

        elif choice == "2":
            filename = input("Arquivo para enviar: ").strip()
            upload(server_ip, port, filename)

        elif choice == "3":
            print("Saindo")
            break

        else:
            print("Opção inválida")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", action="store_true")

    args = parser.parse_args()

    if args.cli:
        cli()
    else:
        print("Use --cli para iniciar o modo interativo")