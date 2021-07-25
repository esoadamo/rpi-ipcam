from select import select
from camera import Camera, CameraBufferAble
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Lock
from time import time
from os import pipe, write, read
from typing import List, Tuple, Dict

NetAddr = Tuple[str, int]


class CameraBuffer(CameraBufferAble):
    def __init__(self) -> None:
        super().__init__()
        self.__buff = bytearray()
        self.__lock_buff = Lock()
        self.__lock_full = Lock()
        self.__pipe = pipe()

    @property
    def read_pipe(self) -> int:
        return self.__pipe[0]

    def write(self, b: bytes) -> None:
        if len(self.__buff) > 4096 * 2:
            self.__lock_full.acquire()
            self.__lock_full.acquire()

        with self.__lock_buff:
            self.__buff.extend(b)
            write(self.__pipe[1], b'1')

    def read(self) -> bytes:
        with self.__lock_buff:
            r = bytes(self.__buff[:1024**2])
            self.__buff = self.__buff[1024**2:]
        while self.__lock_full.locked():
            self.__lock_full.release()

        return r


def open_stream_server(port: int = 8442) -> None:
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.setblocking(False)
    server_socket.bind(('', port))

    cam = Camera()
    cam_buff = CameraBuffer()

    subscribed_clients: Dict[NetAddr, int] = dict()  # addr: last ping request

    while True:
        readers, _, _ = select([server_socket, cam_buff.read_pipe], [], [], 1)  # type: List[socket], List[socket], List[socket]

        for reader in readers:
            if reader == server_socket:
                message, address = server_socket.recvfrom(32)  # type: bytes, NetAddr
                if b'login' in message:
                    print('new subscription', address)

                    if not subscribed_clients:
                        print('starting recording')
                        cam.start_stream(cam_buff)

                    subscribed_clients[address] = int(time())
                elif b'ping' in message:
                    subscribed_clients[address] = int(time())
            elif reader == cam_buff.read_pipe:
                print('sending data')
                read(cam_buff.read_pipe, 4096)
                cam_data = cam_buff.read()
                for client_addr in subscribed_clients.keys():
                    server_socket.sendto(cam_data, client_addr)

        timed_out_clients: List[NetAddr] = []
        for client_addr, client_last_time in subscribed_clients.items():
            if time() - client_last_time > 30:
                timed_out_clients.append(client_addr)

        for client_addr in timed_out_clients:
            print('client timed out', client_addr)
            del subscribed_clients[client_addr]

        if timed_out_clients and not subscribed_clients:
            print('stopping recording')
            cam_buff.stop()
            cam_buff.read()


if __name__ == '__main__':
    print('opening stream server')
    open_stream_server()
