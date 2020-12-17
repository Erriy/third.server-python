#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import os
import redis
import time


admin_fingerprint = os.environ.get("ADMIN_FINGERPRINT", "")
if '' == admin_fingerprint:
    raise "未配置管理员信息，拒绝启动"



def retry(func, times=10, interval=1, description=''):
    success = False
    error = ''
    
    description = description if description else func.__name__


    print('正在检查"%s"服务是否可连接')
    for i in range(times):
        try:
            func()
            success = True
            break
        except e:
            time.sleep(interval)
            error = e
            continue
    
    if success:
        pass



while True:
    try:
        rds = redis.Redis(
            host=os.environ.get("REDIS_HOST", "127.0.0.1"),
            port=int(os.environ.get("REDIS_PORT", 6379)),
            decode_responses=True
        )
    except err:
        time.sleep(1)
        continue








