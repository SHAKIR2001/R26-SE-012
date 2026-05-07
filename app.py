from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify

from config import MAX_CONTENT_LENGTH
from predictors import blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    for bp in blueprints:
        app.register_blueprint(bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"error": "Image too large. Max 10 MB."}), 413

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5005)
