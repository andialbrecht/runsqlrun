import json
import os

from xdg import BaseDirectory

CONFIG_FILE = os.path.join(BaseDirectory.save_config_path('runsqlrun'),
                           'config.json')

name = 'runsqlrun'
version = '0.4.2-dev0'
description = 'A database UI.'
author = 'Andi Albrecht'
author_email = 'albrecht.andi@gmail.com'
url = 'http://runsqlrun.org'


def load():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        data = json.load(f)
    return data


def save(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)
