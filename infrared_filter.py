from PIL.Image import Image


class __MeanCalculator:
    def __init__(self, initial: float = 0):
        self.__n: int = 0
        self.__val: float = initial

    def __add__(self, other: float) -> "__MeanCalculator":
        self.__val = ((self.__val * self.__n) + other) / (self.__n + 1)
        self.__n += 1
        return self

    def __str__(self) -> str:
        return f"Mean({self.value})"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def value(self) -> float:
        return self.__val


def infrared_filter(image: Image) -> Image:
    """
    Removes infrared interference from the image
    :param image: image with red pollution from IR light
    :return: image without IR pollution
    """
    image_new = image.copy()

    red_mean = __MeanCalculator()
    green_mean = __MeanCalculator()
    blue_mean = __MeanCalculator()

    for y in range(image_new.size[1]):
        for x in range(image_new.size[0]):
            pixel = image_new.getpixel((x, y))
            r, g, b = pixel[0], pixel[1], pixel[2]
            red_mean += r
            blue_mean += b
            green_mean += g

    coefficient_red = 128 / red_mean.value
    coefficient_green = 128 / green_mean.value
    coefficient_blue = 128 / blue_mean.value

    for y in range(image_new.size[1]):
        for x in range(image_new.size[0]):
            pixel = image_new.getpixel((x, y))
            r, g, b = pixel[0], pixel[1], pixel[2]
            r *= coefficient_red
            g *= coefficient_green
            b *= coefficient_blue
            image_new.putpixel((x, y), (int(r), int(g), int(b)))

    return image_new


def main() -> int:
    from pathlib import Path
    from sys import argv
    from PIL import Image

    try:
        file_from = Path(argv[1])
        file_to = Path(argv[2])
    except IndexError:
        print('ERR: File from/to/both not specified')
        return 1

    if not file_from.is_file():
        print('ERR: Given from file does not exist')
        return 1

    img_from = Image.open(file_from)
    img_to = infrared_filter(img_from)
    with file_to.open('wb') as f:
        img_to.save(f, 'png')


if __name__ == '__main__':
    exit(main())
