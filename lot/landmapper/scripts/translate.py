#!/bin/env python
from __future__ import print_function
import sys
import json


def translate(content, wdict):
    for key in wdict:
        content = content.replace(key, wdict[key])
    return content


if __name__ == '__main__':
    content_path = sys.argv[1]
    field_map_path = sys.argv[2]

    wdict = json.loads(open(field_map_path, 'r').read())
    content = open(content_path, 'r').read()

    print(translate(content, wdict))
