import struct


RRQ = 1
WRQ = 2
DATA = 3
ACK = 4
ERROR = 5

DEFAULT_MODE = "octet"
MAX_DATA_SIZE = 512

ERROR_MESSAGES = {
    0: "Not defined",
    1: "File not found",
    2: "Access violation",
    3: "Disk full or allocation exceeded",
    4: "Illegal TFTP operation",
    5: "Unknown transfer ID",
    6: "File already exists",
    7: "No such user",
}


def build_rrq(filename, mode=DEFAULT_MODE):
    return struct.pack(f"!H", RRQ) + filename.encode() + b"\x00" + mode.encode() + b"\x00"


def build_wrq(filename, mode=DEFAULT_MODE):
    return struct.pack(f"!H", WRQ) + filename.encode() + b"\x00" + mode.encode() + b"\x00"


def build_data(block_number, data):
    return struct.pack("!HH", DATA, block_number) + data


def build_ack(block_number):
    return struct.pack("!HH", ACK, block_number)


def build_error(error_code, message=""):
    if not message:
        message = ERROR_MESSAGES.get(error_code, "Unknown error")
    return struct.pack("!HH", ERROR, error_code) + message.encode() + b"\x00"


def parse_packet(data):
    opcode = struct.unpack("!H", data[:2])[0]

    if opcode in (RRQ, WRQ):
        parts = data[2:].split(b"\x00")
        return {
            "opcode": opcode,
            "filename": parts[0].decode(),
            "mode": parts[1].decode(),
        }

    if opcode == DATA:
        block_number = struct.unpack("!H", data[2:4])[0]
        return {
            "opcode": opcode,
            "block_number": block_number,
            "data": data[4:],
        }

    if opcode == ACK:
        block_number = struct.unpack("!H", data[2:4])[0]
        return {
            "opcode": opcode,
            "block_number": block_number,
        }

    if opcode == ERROR:
        error_code = struct.unpack("!H", data[2:4])[0]
        message = data[4:-1].decode()
        return {
            "opcode": opcode,
            "error_code": error_code,
            "message": message,
        }

    raise ValueError(f"Unknown opcode: {opcode}")
