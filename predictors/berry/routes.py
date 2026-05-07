from flask import Blueprint

from predictors.berry.predictor import predictor
from predictors.utils import run_prediction

bp = Blueprint("berry", __name__, url_prefix="/predict")


@bp.post("/berry")
def predict_berry():
    """Classify a pepper berry: healthy vs lace bug damage."""
    return run_prediction(predictor, "berry")
