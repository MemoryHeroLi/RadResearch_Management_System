import os

from flask import Flask

from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    # 导入模型以让 create_all 可见
    import models  # noqa: F401

    # 注册蓝图（在各任务中逐步引入；先注册 dashboard）
    from blueprints.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from blueprints.business import business_bp
    app.register_blueprint(business_bp, url_prefix="/business")

    from blueprints.team import team_bp
    app.register_blueprint(team_bp, url_prefix="/team")

    from blueprints.process import process_bp
    app.register_blueprint(process_bp, url_prefix="/process")

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
