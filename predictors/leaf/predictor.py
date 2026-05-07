from predictors.base import BasePredictor
from predictors.leaf import config


class LeafPredictor(BasePredictor):
    model_path = config.MODEL_PATH
    classes = config.CLASSES
    description = config.DESCRIPTION


predictor = LeafPredictor()
