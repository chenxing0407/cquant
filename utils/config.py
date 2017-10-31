# -*- coding: utf-8 -*-

import yaml

cfg = {}


def get_config():
    global cfg
    with open('../config.yaml') as f:
        cfg = yaml.load(f)
    # print(cfg)

get_config()

if __name__ == '__main__':
    get_config()
