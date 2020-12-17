#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import os
import redis
import time
import logging
from py2neo import Graph
from functools import wraps


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt=r'%Y-%m-%d %I:%M:%S')



def retry(times=10, interval=1, description=''):
    def __wrapper(func):
        @wraps(func)
        def __do():
            error = ''
            logging.info('[*]正在检查"%s"服务是否可连接'%(description))
            for i in range(times):
                try:
                    func()
                    logging.info('[*]"%s"服务连接测试成功'%(description))
                    return
                except Exception as e:
                    if i!=times-1:
                        logging.info('[.]"%s"服务第%d次连接失败，%d秒后继续尝试'%(description, i, interval))
                    else:
                        logging.info('[.]"%s"服务第%d次连接失败'%(description, i))
                    time.sleep(interval)
                    error = e
                    continue
            logging.info('[!]"%s"服务无法连接，请确认后再重新启动本服务'%(description))
            raise error
        return __do
    return __wrapper


@retry(times=10, interval=2, description='redis')
def redis_connect():
    redis.Redis(
        host=os.environ.get("REDIS_HOST", "127.0.0.1"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        decode_responses=True
    ).close()


@retry(times=10, interval=3, description='neo4j')
def neo4j_connect():
    host = str(os.environ.get("NEO_HOST", "127.0.0.1"))
    port = int(os.environ.get("NEO_PORT", 7687))
    user = str(os.environ.get("NEO_USER", "neo4j"))
    password = str(os.environ.get("NEO_PASS", r"ub1JOnQcuV^rfBsr5%Ek"))

    Graph(host=host, port=port, auth=(user, password)).run('match (n) return n limit 1')



admin_fingerprint = os.environ.get("ADMIN_FINGERPRINT", "")
if '' == admin_fingerprint:
    raise "未配置管理员信息，拒绝启动"
redis_connect()
neo4j_connect()

