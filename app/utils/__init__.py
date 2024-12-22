from .config import Settings
import uuid


def generate_uuid():
    return uuid.uuid5(uuid.NAMESPACE_DNS, Settings.DOMAIN_NAME)
