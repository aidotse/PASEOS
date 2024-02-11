import binascii


def compute_CRC(my_string):
    """Comput Cyclic Redundancy Check (CRC) of input.

    Args:
        my_string (str): input string.

    Returns:
        str: CRC of input.
    """
    return str(binascii.crc32(str(my_string).encode()))


def check_CRC(string_payload, crc_expected, payload_in_byte_format=False):
    """Compute CRC of payload string and compare it with the received one.

    Args:
        string_payload (str/byte): input string. Can be either string/byte.
        crc_expected (str): received CRC.
        payload_in_byte_format (bool, optional): if True, payload in byte format; else string. Defaults to False.

    Returns:
        bool: if CRC check completed successfully.
    """
    if not (payload_in_byte_format):
        return binascii.crc32(string_payload.encode()) == int(crc_expected)
    else:
        return binascii.crc32(string_payload) == int(crc_expected)


def receive_ACK(conn, buffer_size):
    """Receiving Acknowledgement (ACK).

    Args:
        conn (socket): communication socket.
        buffer_size (int): communication buffer size.

    Returns:
        bool: True if ACK is received. False in all the other cases.
    """
    # Wait for ACK
    ack = conn.recv(buffer_size)
    ack = ack.decode("utf-8")

    if ack == "ACK":
        return True
    else:
        return False


def send_with_CRC(conn, payload_string, buffer_size):
    """Send string with CRC check.

    Args:
        conn (socket): communication socket.
        payload_string (str): payload string to send.
        buffer_size (int): communication buffer size.
    """
    crc = compute_CRC(payload_string)
    transmit_string = str(payload_string) + "\n" + crc
    ack_received = False
    while not (ack_received):
        conn.sendall(transmit_string.encode())
        ack_received = receive_ACK(conn, buffer_size)


def receive_with_CRC(conn, buffer_size):
    """Receive string with CRC check.

    Args:
        conn (socket): communication socket.
        buffer_size (int): communication buffer size.

    Returns:
        str: received string.
    """
    crc_ok = False

    while not (crc_ok):
        # receive image size
        received_string = conn.recv(buffer_size)

        # Transform to string
        received_string = received_string.decode("utf-8")

        # Get CRC
        crc_expected = received_string.split("\n")[-1]

        # Payload string
        string_payload = received_string.replace(received_string.split("\n")[-1], "")[
            :-1
        ]

        if check_CRC(string_payload, crc_expected, payload_in_byte_format=False):
            conn.sendall(b"ACK")
            crc_ok = True
        else:
            conn.sendall(b"NACK")

    return string_payload
