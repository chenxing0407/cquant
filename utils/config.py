# -*- coding: utf-8 -*-

import yaml
from os import path
cfg = {}


def get_config():
    global cfg
    with open(path.join(path.dirname(__file__), '../config.yaml')) as f:
        cfg = yaml.load(f)
    # print(cfg)

get_config()

if __name__ == '__main__':
    get_config()
