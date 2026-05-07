from flask import Blueprint

from predictors.leaf.predictor import predictor
from predictors.utils import run_prediction

bp = Blueprint("leaf", __name__, url_prefix="/predict")


@bp.post("/leaf")
def predict_leaf():
    """Classify a pepper leaf across 4 disease categories."""
    return run_prediction(predictor, "leaf")
