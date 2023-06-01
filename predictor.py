import torch
import numpy as np

from detectron2.data import MetadataCatalog
from detectron2.engine.defaults import DefaultPredictor
from detectron2.utils.visualizer import ColorMode, Visualizer
from detectron2.config import get_cfg
from skimage.segmentation import slic
from skimage.util import img_as_float

CONFIG_FILE = "detectron2/configs/fcos/fcos_imprv_R_101_FPN_cpu.yaml"
# CONFIG_FILE = "src/detectron2/configs/fcos/fcos_imprv_R_101_FPN.yaml"

CONFIDENCE_THRESHOLD = 0.5


def setup_cfg():
    # Load default config
    cfg = get_cfg()
    # Merge the default with customized one
    cfg.merge_from_file(CONFIG_FILE)
    # Set score_threshold for builtin models
    cfg.MODEL.RETINANET.SCORE_THRESH_TEST = CONFIDENCE_THRESHOLD
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = CONFIDENCE_THRESHOLD
    cfg.MODEL.FCOS.INFERENCE_TH = CONFIDENCE_THRESHOLD
    cfg.freeze()

    return cfg


class VisualizationDemo(object):
    def __init__(self, instance_mode=ColorMode.IMAGE):
        """
        Args:
            instance_mode (ColorMode):
            parallel (bool): whether to run the model in different processes from visualization.
                Useful since the visualization logic can be slow.
        """
        self.cfg = setup_cfg()
        self.metadata = MetadataCatalog.get(
            self.cfg.DATASETS.TEST[0] if len(self.cfg.DATASETS.TEST) else "__unused"
        )
        self.cpu_device = torch.device("cpu")
        self.instance_mode = instance_mode

        self.predictor = DefaultPredictor(self.cfg)

    def run_on_image(self, image, click_point):
        """
        Infer a single image.
        For each inference, just segment an instance that user clicked on.

        Args:
            image (np.ndarray): an image of shape (H, W, C) (in BGR order).
                This is the format used by OpenCV.
            click_point (tuple: (y,x)): where user clicked on selected region.
                It's used to select one and ignore others.
        Returns:
            predictions (dict): the output of the model.
            vis_output (VisImage): the visualized image output.
        """
        vis_output = None
        predictions = self.predictor(image, click_point)
        # Convert image from OpenCV BGR format to Matplotlib RGB format.
        image = image[:, :, ::-1]

        mask = (
            predictions["instances"].raw_masks.squeeze(1).data.cpu().numpy()
            if predictions["instances"].has("raw_masks")
            else None
        )
        mask_bo = (
            predictions["instances"].pred_masks_bo.squeeze(1).data.cpu().numpy()
            if predictions["instances"].has("pred_masks_bo")
            else None
        )
        bound_bo = (
            predictions["instances"].pred_bounds_bo.squeeze(1).data.cpu().numpy()
            if predictions["instances"].has("pred_bounds_bo")
            else None
        )
        bound = (
            predictions["instances"].pred_bounds.squeeze(1).data.cpu().numpy()
            if predictions["instances"].has("pred_bounds")
            else None
        )

        visualizer = Visualizer(image, self.metadata, instance_mode=self.instance_mode)
        if "instances" in predictions:
            instances = predictions["instances"].to(self.cpu_device)
            vis_output = visualizer.draw_instance_predictions(predictions=instances)

        return predictions, vis_output


class SLICSuperpixels:
    """
    Apply sklearn's SLIC algorithm to segment the image into numerous superpixels.

    Reference: https://scikit-image.org/docs/dev/api/skimage.segmentation.html#skimage.segmentation.slic
    """

    def __init__(self, image):
        self.image = image
        self.segments = None

    def segmentImage(self, k=1951, m=35):
        self.segments = slic(img_as_float(self.image), n_segments=k, compactness=m)

    def mapping(self, cluster_idx):
        assert self.segments is not None
        rows, cols = np.where(self.segments == cluster_idx)
        return np.vstack((rows, cols))

    def getCluster(self, pos):
        (y, x) = pos
        cluster_idx = self.segments[y, x]
        return self.mapping(cluster_idx)
