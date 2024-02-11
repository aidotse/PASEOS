import socket
import binascii

def compute_CRC(my_string):
    return str(binascii.crc32(str(my_string).encode()))

def check_CRC(string_payload, crc_expected, payload_in_byte_format=False):
    if not(payload_in_byte_format):
        return binascii.crc32(string_payload.encode()) == int(crc_expected)
    else:
        return binascii.crc32(string_payload) == int(crc_expected)

def receive_ACK(conn, buffer_size):
    # Wait for ACK
    ack = conn.recv(buffer_size)
    ack = ack.decode('utf-8')

    if ack == "ACK":
        return True
    else:
        return False

def send_with_CRC(conn, my_string, buffer_size):
    crc = compute_CRC(my_string)
    transmit_string = str(my_string) + '\n' + crc
    ack_received = False
    while not(ack_received):
        conn.sendall(transmit_string.encode())
        ack_received = receive_ACK(conn, buffer_size)


def receive_with_CRC(conn, buffer_size):
    crc_ok = False

    while not(crc_ok):
        # receive image size
        received_string = conn.recv(buffer_size)

        # Transform to string
        received_string = received_string.decode('utf-8')

        # Get CRC
        crc_expected = received_string.split('\n')[-1]

        # Payload string
        string_payload = received_string.replace(received_string.split("\n")[-1],"")[:-1]

        if check_CRC(string_payload, crc_expected, payload_in_byte_format=False):
            conn.sendall(b"ACK")
            crc_ok = True
        else:
            conn.sendall(b"NACK")


    return string_payload