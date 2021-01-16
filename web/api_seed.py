#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import json
import time
from flask import Blueprint, request
from web_common import build_response, assert_check, neo4j, dumps, loads


seed = Blueprint("seed", __name__)


@seed.route('', methods=['PUT'])
def api_create():
    print(request.json)
    return build_response()


@seed.route('', methods=['GET'])
def api_search():
    print(request.args)
    return build_response()


@seed.route('<string:seedid>', methods=['DELETE'])
def api_delete(seedid):
    print(request.path)
    return build_response()

