import pytest
import os


@pytest.fixture()
def app(tmp_path):
    """内存数据库的测试 app，复用生产工厂但通过环境变量切换为内存库"""
    # 必须在 create_app() 之前设置，Config 会读取此环境变量
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    from start import create_app

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    with app.app_context():
        from extensions import db as _db
        yield _db
