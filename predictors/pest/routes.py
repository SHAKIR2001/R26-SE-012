from flask import Blueprint

from predictors.pest.predictor import predictor
from predictors.utils import run_prediction

bp = Blueprint("pest", __name__, url_prefix="/predict")


@bp.post("/pest")
def predict_pest():
    """Identify pests on a pepper plant across 4 pest categories."""
    return run_prediction(predictor, "pest")
