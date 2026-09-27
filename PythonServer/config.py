import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_PATH) as f:
    _config = json.load(f)

DEVICE_KEY = _config["device_key"]
SENDERS = _config["senders"]
PORT = _config.get("port", 5000)
