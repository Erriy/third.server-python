#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import os









admin_fingerprint = os.environ.get("ADMIN_FINGERPRINT", "")
if not admin_fingerprint:
    raise "未配置管理员信息，拒绝启动"
    os._exit(-1)














