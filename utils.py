import numpy as np
import base64
import re

from PIL import Image
from io import BytesIO
from PIL import Image, ImageDraw


def base64_to_pil(img_base64):
    """
    Convert base64 image data to PIL image

    Args:
        img_base64: image in base64 string format.

    Returns:
        pil_image: PIL image.
    """
    image_data = re.sub("^data:image/.+;base64,", "", img_base64)
    pil_image = Image.open(BytesIO(base64.b64decode(image_data)))
    return pil_image


def np_to_base64(img_np):
    """
    Convert numpy image (RGB) to base64 string

    Args:
        img_np: image as a numpy array

    Returns: image represented in base64
    """
    img = Image.fromarray(img_np.astype("uint8"), "RGB")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode(
        "ascii"
    )


def polygons_to_bitmask(polygons, height, width):
    """
    Convert a list of polygon vertices to a numpy binary mask

    Args:
        polygons (list(list)): vertices [[(x0, y0), (x1, y1),...]] or [[x0, y0, x1, y1,...]]
        width: width of mask
        height: height of mask
    Returns:
        mask: an np.ndarray of 0 and 1 (binary mask)
    """

    mask = Image.new("L", (width, height), 0)
    for polygon in polygons:
        ImageDraw.Draw(mask).polygon(polygon, outline=1, fill=1)
    mask = np.array(mask)
    return mask


def region_inference(image, top_left, bot_right, demo, click_point):
    """
    Predict and get maskes for a region of the original image

    Args:
        image: a full-size image currently worked on
        top_left: the top left point of the infered region
        bot_right: the bottome right of the infered region
        demo: model for inference
    Returns:
        infered_region: region with mask
        mask_pos: numpy array storing positions of each mask-point,
                return None if no instance exists
    """
    y0, x0 = top_left
    y1, x1 = bot_right
    crop_region = image[y0:y1, x0:x1, :]
    predictions = None
    try:
        predictions, visualized_output = demo.run_on_image(crop_region, click_point)
    except:
        pass
    if predictions is not None:
        infered_region = visualized_output.get_image()[:, :, ::-1]
        return infered_region, predictions
    else:
        return crop_region, None
