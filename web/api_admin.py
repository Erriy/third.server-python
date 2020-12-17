#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import os
from flask import Blueprint, request
from functools import partial
from api_pubkey import verify
from web_common import admin_fingerprint, build_response


admin = Blueprint("admin", __name__)
admin_verify = partial(verify, require=True, auth_check=lambda fp: fp == admin_fingerprint)



@admin.route('', methods=['GET'])
@admin_verify()
def api_test():
    return build_response(success=True)





