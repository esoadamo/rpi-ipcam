from flask import Flask, send_from_directory, Response
from camera import Camera, CameraBufferAble
from pathlib import Path

app = Flask(__name__)
camera = Camera()
script_dir = Path(__file__).parent.absolute()


@app.route('/cam/img/full.jpg')
def web_img_jpg():
    file = camera.get_image(auto_delete=True)
    return send_from_directory(file.parent, file.name)


@app.route('/cam/img/low.jpg')
def web_img_jpg_low():
    file = camera.get_image(auto_delete=True, resolution=(648, 486))
    return send_from_directory(file.parent, file.name)


@app.route('/cam/vid.h264')
def web_vid_h264():
    buffer = CameraBufferAble(16 * 1024**2)
    buffer.start(camera)
    return Response(buffer.stream(), content_type="application/octet-stream")


@app.route('/cam/img')
def web_img():
    return send_from_directory(script_dir, 'img.html')


if __name__ == '__main__':
    app.run(port=8441)
