from flask import Flask, request, render_template, jsonify
from utils import base64_to_pil, np_to_base64, region_inference
from predictor import VisualizationDemo, SLICSuperpixels
from structures import MasksManager

import os
import numpy as np


app = Flask(__name__)

# demo = None
demo = VisualizationDemo()
masks_manager = None


@app.route("/")
@app.route("/index")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST", "GET"])
def get_prediction():
    if request.method == "POST":
        # Get params from request body
        body = request.json
        image = base64_to_pil(body["image"])  # decode image from base64 encoding
        image = np.array(image)
        click_point = (body["clickpoint"][0], body["clickpoint"][1])  # (y,x)

        polygons = body["polygons"]

        masks_manager = MasksManager(image)
        # Convert previous polygons to Mask objects, then add to MasksManager
        masks_manager.addMasksFromPolygons(polygons)

        y0, x0, y1, x1 = body["vertices"]  # top_left, bot_right
        # Model inference
        mask_region, predictions = region_inference(
            image, (y0, x0), (y1, x1), demo, click_point
        )

        # Add mask and redraw new image with new mask
        if predictions is not None and predictions["instances"].has("pred_masks"):
            bit_mask = (
                predictions["instances"].pred_masks[0].squeeze(1).data.cpu().numpy()
            )
            masks_manager.addMask(bit_mask, (y0, x0))

            pred_polygons = masks_manager.getPolygons(-1)
            polygons.append(pred_polygons)
        image = masks_manager.redrawAllMasks()
        # image = masks_manager.redrawAllPolygonMasks(polygons)

        # Refactor returned parameters
        # encode array of image to base64
        image = np_to_base64(image)

        return jsonify(image=image, polygons=polygons)
    return None


@app.route("/remove", methods=["POST", "GET"])
def remove_mask():
    if request.method == "POST":
        body = request.json
        image = base64_to_pil(body["image"])
        image = np.array(image)

        y, x = (body["clickpoint"][0], body["clickpoint"][1])  # (y,x)
        polygons = body["polygons"]

        # polygons = [[np.asarray(polygon, dtype=np.int32)] for polygon in polygons]
        masks_manager = MasksManager(image)
        masks_manager.addMasksFromPolygons(polygons)

        mask_id = masks_manager.getMaskID(y, x)  # Get index of removed mask
        image = masks_manager.removeMask(mask_id)  # Redraw image
        if mask_id != -1000:  # dummy value
            polygons.pop(mask_id)  # List of polygons is modified

        image = np_to_base64(image)
        # polygons = [polygon[0].tolist() for polygon in polygons]

        return jsonify(image=image, polygons=polygons)
    return None


@app.route("/include", methods=["POST", "GET"])
def include():
    if request.method == "POST":
        body = request.json
        image = base64_to_pil(body["image"])
        image = np.array(image)

        y, x = body["clickpoint"][0], body["clickpoint"][1]  # (y,x)
        polygons = body["polygons"]

        # polygons = [[np.asarray(polygon, dtype=np.int32)] for polygon in polygons]
        masks_manager = MasksManager(image)
        masks_manager.addMasksFromPolygons(polygons)

        slic = SLICSuperpixels(image)
        slic.segmentImage(k=1951, m=35)
        cluster = slic.getCluster((y, x))

        image = masks_manager.includeClickHandle(cluster)
        polygons[-1] = masks_manager.getPolygons(-1)

        image = np_to_base64(image)

        return jsonify(image=image, polygons=polygons)
    return None


@app.route("/exclude", methods=["POST", "GET"])
def exclude():
    if request.method == "POST":
        body = request.json
        image = base64_to_pil(body["image"])
        image = np.array(image)

        y, x = body["clickpoint"][0], body["clickpoint"][1]  # (y,x)
        polygons = body["polygons"]

        masks_manager = MasksManager(image)
        masks_manager.addMasksFromPolygons(polygons)

        slic = SLICSuperpixels(image)
        slic.segmentImage(k=2391, m=35)
        cluster = slic.getCluster((y, x))

        image = masks_manager.excludeClickHandle(cluster)
        polygons[-1] = masks_manager.getPolygons(-1)

        image = np_to_base64(image)
        return jsonify(image=image, polygons=polygons)
    return None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
