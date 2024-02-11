import socket
import binascii
from PIL import Image
import io
import numpy as np
from communication_protocol import check_CRC, send_with_CRC, receive_with_CRC

def create_connection(ip_client, port, buffer_size):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"Binding connection at address: {ip_client} and port: {port}...")
        s.bind((ip_client, port))
        print("Waiting incoming connection...")
        s.listen()
        conn, addr = s.accept()
        print(f"Connected by {addr}")
        # Create first handshake
        ack = conn.recv(buffer_size)
        print(f"{ack.decode('utf-8')} received.")
        conn.sendall(b"ACK!")
        return conn


def sync_with_spacecraft(conn, local_time, buffer_size):

    # Receive spacecraft time with CRC
    spacecraft_time = receive_with_CRC(conn, buffer_size)

    # Transmit local time with CRC
    send_with_CRC(conn, str(local_time), buffer_size)

    return spacecraft_time

def receive_image(conn, buffer_size):

    # Receive metadata with CRC check
    image_metadata = receive_with_CRC(conn, buffer_size)

    image_size = int(image_metadata.split('\n')[0])

    # Get image name
    image_name = image_metadata.split('\n')[1]

    print(f"Receiving image:\n\bImage name: {image_name}.\n\bImage size: {image_size}.")

    print("First handshake successful. Starting receiving image.")

    # Create a buffer
    data = b""

    # Received
    received = 0

    while(received < image_size):

        # Calculate bytes to receive
        bytes_to_receive = min(buffer_size, image_size - received)
        # Receive data
        data_buffer = conn.recv(bytes_to_receive)

        # Receive CRC
        crc_expected = conn.recv(buffer_size)

        # Check CRC and send ACK if correct
        if check_CRC(data_buffer, crc_expected, payload_in_byte_format=True):
            conn.sendall(b"ACK")
            data += data_buffer
            received += len(data_buffer)
            print("ACK received.")
            print(f"Received bytes: {received}.")
        else:
            conn.sendall(b"NACK")



    image = Image.open(io.BytesIO(data))
    print("Image received successfully.")

    return  np.array(image), image_name