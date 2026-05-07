from predictors.base import BasePredictor
from predictors.pest import config


class PestPredictor(BasePredictor):
    model_path = config.MODEL_PATH
    classes = config.CLASSES
    description = config.DESCRIPTION


predictor = PestPredictor()
