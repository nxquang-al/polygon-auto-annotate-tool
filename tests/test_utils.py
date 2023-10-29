import numpy as np

from src.utils.utils import base64_to_pil, np_to_base64


def test_np_to_base64():
    array = np.ones((10, 10, 3))
    encoded_string = np_to_base64(array)

    assert encoded_string.startswith("data:image/png;base64")


def test_base64_to_pil():
    image_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAFElEQVR4nGNkZGRkwA2Y8MiNYGkAEO4AF8pTEvwAAAAASUVORK5CYII="
    pil_image = base64_to_pil(image_data)
    assert pil_image.size == (10, 10)
