from typing import Optional, Tuple, Iterator, Union
from pathlib import Path
from tempfile import mkstemp
from os import close
from time import time, sleep
from threading import Thread, Lock, Event

# noinspection PyUnresolvedReferences
from picamera import PiCamera


class CameraBufferAble:
    def __init__(self, max_size: Optional[int] = None):
        self.__buff = bytearray()
        self.__max_size = max_size
        self.__curr_size = 0
        self.__lock = Lock()
        self.__signal_write = Event()
        self._camera: Optional[PiCamera] = None

    def write(self, b: Union[bytes, bytearray]) -> int:
        available_size = min(self.__max_size - len(self.__buff), len(b)) if self.__max_size is not None else len(b)
        if available_size > 0:
            with self.__lock:
                self.__buff.extend(b[:available_size])
            self.__signal_write.set()
            return available_size
        return 0

    def read(self, size: Optional[int] = None) -> bytearray:
        self.__wait_readable()
        with self.__lock:
            size = min(size if size is not None else len(self.__buff), len(self.__buff))
            r = self.__buff[:size]
            self.__buff = self.__buff[size:]
            return r

    def __wait_readable(self) -> None:
        lock_acquired_here = False
        try:
            self.__lock.acquire()
            lock_acquired_here = True
            if not self.__buff:
                self.__lock.release()
                lock_acquired_here = False
                self.__signal_write.wait()
                self.__signal_write.clear()
        finally:
            if lock_acquired_here:
                self.__lock.release()

    def stream(self) -> Iterator[bytes]:
        try:
            while True:
                yield bytes(self.read())
        finally:
            self.stop()

    def start(self, camera: "Camera") -> None:
        return camera.start_stream(self)

    def stop(self) -> None:
        if self._camera is not None:
            self._camera.stop_recording()
        self.__buff.clear()


class Camera:
    def __init__(self):
        self.__cam: Optional[PiCamera] = None
        self.__dir = Path('/ram/')

        self.__image_ttl = 1 / 15
        self.__last_image_time = time()
        self.__last_image_path: Optional[Path] = None
        self.__camera_lock: Lock = Lock()
        self.__camera_timeout: int = 0

    def get_image(self, auto_delete: bool = False, resolution: Optional[Tuple[int, int]] = None) -> Path:
        self.__create_camera()
        with self.__camera_lock:
            return self.__get_image(auto_delete, resolution=resolution)

    def get_video(self, auto_delete: bool = False) -> Path:
        self.__create_camera()
        with self.__camera_lock:
            return self.__get_video(auto_delete)

    def start_stream(self, writable: CameraBufferAble) -> None:
        self.__create_camera()
        with self.__camera_lock:
            writable._camera = self.__cam
            self.__cam.start_recording(writable, 'h264')

    def __create_camera(self) -> None:
        with self.__camera_lock:
            self.__camera_timeout = 300
            if self.__cam is not None:
                return
            self.__cam = PiCamera()

            def job_camera_timeout():
                while True:
                    sleep(10)
                    with self.__camera_lock:
                        if self.__camera_timeout <= 0:
                            self.__cam.close()
                            self.__cam = None
                            break

            Thread(target=job_camera_timeout).start()

    def __get_image(self, auto_delete: bool = False, resolution: Optional[Tuple[int, int]] = None) -> Path:
        if self.__last_image_path is not None and time() < self.__last_image_time + self.__image_ttl:
            return self.__last_image_path

        self.__cam.resolution = (2592, 1944) if resolution is None else resolution
        self.__cam.framerate = 15

        fd, str_path = mkstemp(suffix='.jpg', dir=f"{self.__dir.absolute()}")
        close(fd)
        self.__cam.capture(str_path)
        path = Path(str_path)
        self.__last_image_path = path
        self.__last_image_time = time()

        if auto_delete:
            def job_auto_delete():
                sleep(float(2 * self.__image_ttl))
                path.unlink()

            Thread(target=job_auto_delete).start()

        return path

    def __get_video(self, auto_delete: bool) -> Path:
        fd, str_path = mkstemp(suffix='.h264', dir=f"{self.__dir.absolute()}")
        close(fd)

        self.__cam.resolution = (1920, 1080)
        self.__cam.framerate = 30

        self.__cam.start_recording(str_path)
        sleep(15)
        self.__cam.stop_recording()

        path = Path(str_path)

        if auto_delete:
            def job_auto_delete():
                sleep(2)
                path.unlink()

            Thread(target=job_auto_delete).start()

        return path
