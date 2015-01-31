import json
import os

from xdg import BaseDirectory

CONFIG_FILE = os.path.join(BaseDirectory.save_config_path('runsqlrun'),
                           'config.json')


def load():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        data = json.load(f)
    return data


def save(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)
