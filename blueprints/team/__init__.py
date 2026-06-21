from flask import Blueprint

team_bp = Blueprint("team", __name__)

from blueprints.team import routes  # noqa: E402,F401
