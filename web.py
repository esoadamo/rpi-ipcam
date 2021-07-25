from flask import Flask, send_from_directory
from camera import Camera
from pathlib import Path

app = Flask(__name__)
camera = Camera()
script_dir = Path(__file__).parent.absolute()


@app.route('/cam/img.jpg')
def web_img_jpg():
    file = camera.get_image(auto_delete=True)
    return send_from_directory(file.parent, file.name)


@app.route('/cam/img/low.jpg')
def web_img_jpg_low():
    file = camera.get_image(auto_delete=True, resolution=(648, 486))
    return send_from_directory(file.parent, file.name)


@app.route('/cam/vid.h264')
def web_vid_h264():
    file = camera.get_video(auto_delete=True)
    return send_from_directory(file.parent, file.name, mimetype="video/h264")


@app.route('/cam/img')
def web_img():
    return send_from_directory(script_dir, 'img.html')


if __name__ == '__main__':
    app.run(port=8441)
