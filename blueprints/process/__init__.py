from flask import Blueprint

process_bp = Blueprint("process", __name__)

from blueprints.process import routes  # noqa: E402,F401
