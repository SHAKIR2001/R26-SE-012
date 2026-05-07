from predictors.berry.routes import bp as berry_bp
from predictors.leaf.routes import bp as leaf_bp
from predictors.pest.routes import bp as pest_bp
from predictors.ai.routes import bp as vision_bp

# Add a new model: create its folder, then append its bp here
blueprints = [berry_bp, leaf_bp, pest_bp, vision_bp]
