from socket import socket, SOCK_DGRAM, AF_INET
from select import select


def connect_stream(host: str, port: int) -> None:
    addr = (host, port)
    client_socket = socket(AF_INET, SOCK_DGRAM)
    client_socket.sendto(b'login', addr)

    print('waiting for data')
    with open('/ram/stream.h264', 'wb') as f:
        while True:
            select([client_socket], [], [])
            data, _ = client_socket.recvfrom(1024**2)
            print('data')
            f.write(data)


if __name__ == '__main__':
    print('connecting to the stream')
    connect_stream('10.1.1.113', 8442)
