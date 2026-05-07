from predictors.base import BasePredictor
from predictors.berry import config


class BerryPredictor(BasePredictor):
    model_path = config.MODEL_PATH
    classes = config.CLASSES
    description = config.DESCRIPTION


predictor = BerryPredictor()
