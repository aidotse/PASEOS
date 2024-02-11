import socket
import binascii
import io
from PIL import Image
from communication_protocol import receive_ACK, send_with_CRC, receive_with_CRC


def connect_to_server(ip_server, port, buffer_size):
    """Connect to listening server.

    Args:
        ip_server (str): server Internet Protocol (IP) address.
        port (int): communication port.
        buffer_size (int): communication buffer size.

    Returns:
        socket: communication socket.
    """
    print(f"Connecting at address: {ip_server} and port: {port}...")
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((ip_server, port))
    conn.sendall(b"ACK")
    ack = conn.recv(buffer_size)
    print(f"{ack.decode('utf-8')} received.")
    return conn


def sync_with_GS(conn, local_time, buffer_size):
    """Synchornize time with the target ground station (GS). Local time is sent. GS time is received.

    Args:
        conn (socket): communication socket.
        local_time (pykep epoch): local time.
        buffer_size (int): communication buffer size.

    Returns:
        str: GS time in string format.
    """
    # Transmit local time with CRC
    send_with_CRC(conn, str(local_time), buffer_size)

    # Receive ground station time with CRC
    gs_time = receive_with_CRC(conn, buffer_size)

    return gs_time


def send_image(conn, image, image_name, buffer_size):
    """Send an image to a receiving GS.

    Args:
        conn (socket): communication socket.
        image (numpy array): image to send.
        image_name (str): image name.
        buffer_size (int): communication buffer size.
    """

    # image size
    # Convert the numpy array to a PIL Image
    image_PIL = Image.fromarray(image)

    # Convert the PIL Image to bytes
    image_bytes = io.BytesIO()
    image_PIL.save(image_bytes, format="PNG")
    # Image size
    image_bytes = image_bytes.getvalue()
    # Image CRC
    image_metadata = str(len(image_bytes)) + "\n" + image_name

    print(
        f"Transmitting image:\n\bImage name: {image_name}.\n\bImage size: {len(image_bytes)}."
    )

    # Send meta
    send_with_CRC(conn, image_metadata, buffer_size)

    # Handshake successful
    print("First handshake successful. Starting transmission.")
    # Transmitted bytes
    bytes_transmitted = 0
    # Create a buffer
    while bytes_transmitted < len(image_bytes):
        # Buffer end
        buffer_end = min(bytes_transmitted + buffer_size, len(image_bytes))

        # Transmit buffer
        buffer_tx = image_bytes[bytes_transmitted:buffer_end]

        # Transmit image
        conn.sendall(buffer_tx)

        # Calculate CRC
        buffer_crc = str(binascii.crc32(buffer_tx))

        # Send CRC
        conn.sendall(buffer_crc.encode())

        # Wait for ack
        ack_received = receive_ACK(conn, buffer_size)

        if ack_received:
            print("ACK received.")
            bytes_transmitted += buffer_end - bytes_transmitted
            print(f"Transmitted bytes: {bytes_transmitted}.")

    print("Image transmitted successfully.")
