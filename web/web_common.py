#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import json
import os
from adapter.neo4j import adapter

# pubkey support relationships
pubkey_support_relationships = ['follow', 'block']


adpr = adapter(
    host=str(os.environ.get("NEO_HOST", "127.0.0.1")),
    port=int(os.environ.get("NEO_PORT", 7687)),
    user=str(os.environ.get("NEO_USER", "neo4j")),
    password=str(os.environ.get("NEO_PASS", r"ub1JOnQcuV^rfBsr5%Ek"))
)


class ErrorMsg(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self)
        self.code = code
        self.msg = msg


def assert_check(*args):
    """
    参数列表可有两种形式，两种形势下均可省略errcode，默认错误码为400, errmsg 和 errcode位置可呼唤：
    1. value, errmsg, errcode
    2. (value, errmsg, errcode)
    """
    if 2<=len(args)<=3 and isinstance(args[1], (int, str)):
            args = [args]

    for t in args:
        v = t[0]
        if 2 == len(t):
            em = t[1]
            ec = 400
        if 3 == len(t):
            if isinstance(t[1], int):
                ec = t[1]
                em = t[2]
            else:
                ec = t[2]
                em = t[1]
        if not v:
            raise ErrorMsg(ec, em)


def assert_not_empty(**kwargs):
    for n, v in kwargs.items():
        assert_check(v, '参数"%s"不可为空'%(str(n)))


def build_response(code=200, message="操作成功", headers=dict(), **kwargs):
    dret = dict(code=int(code), message=str(message))
    headers["Content-Type"] = "application/json"
    if kwargs:
        dret.update(data=kwargs)
    return json.dumps(dret, ensure_ascii=False), code, headers

