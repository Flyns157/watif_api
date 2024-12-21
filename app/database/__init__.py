import json
import os

from ..models import User


# ====== User data ===== #
def get_users() -> dict[User]:
    with open(os.path.join(os.path.dirname(__file__), "users.json"), "r") as f:
        return json.load(f)
