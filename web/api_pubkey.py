#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import os
import time
import json
import gnupg
import redis
import base64
import inspect
import tempfile
from functools import wraps
from flask import Blueprint, request
from web_common import build_response, assert_not_empty, assert_check, neo4j, pubkey_support_relationships, admin_fingerprint


pubkey = Blueprint('pubkey', __name__)


# redis 初始化
rds = redis.Redis(
    host=os.environ.get("REDIS_HOST", "127.0.0.1"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True
)
rds.config_set("save", "")
# gpg 初始化
__gpg_home = os.environ.get("GPG_HOME", "./data/gpg/")
if not os.path.exists(__gpg_home):
    os.mkdir(__gpg_home)
gpg = gnupg.GPG(gnupghome=__gpg_home)
gpg.encoding = "utf-8"
# reply timeout
reply_timeout = int(os.environ.get('REPLY_TIMEOUT', 60))
reply_timeout = reply_timeout if reply_timeout > 60 else 60


__fingerprint_allow_char_set = set('1234567890ABCDEF')
def check_fingerprint_format(fp):
    assert_check(
        isinstance(fp, str)
            and 40 == len(fp)
            and not (set(fp.upper()) - __fingerprint_allow_char_set),
        'fingerprint格式错误，请确认后再请求'
    )


def check_nonce():
    nonce = str(request.args.get('nonce', ''))
    assert_check(100 >= len(nonce) >= 30, 'nonce长度不合法，要求30-100个字符之间')
    redis_nonce_key = 'nonce.' + base64.b64encode(nonce.encode()).decode()
    assert_check(not rds.exists(redis_nonce_key), 'nonce已被使用，检测到请求重放，拒绝执行')
    rds.setex(redis_nonce_key, reply_timeout, 1)


def check_sign(sign:str, data:str):
    assert_check(
        (sign, "签名信息不能为空"),
        (data, "被签名数据不能为空")
    )
    if not sign.startswith("-----BEGIN PGP SIGNATURE-----"):
        sign = "-----BEGIN PGP SIGNATURE-----\n" + sign + "\n-----END PGP SIGNATURE-----"
    with tempfile.NamedTemporaryFile('w+t') as f:
        f.write(sign)
        f.flush()
        verify = gpg.verify_data(f.name, data.encode("utf-8"))
        assert_check(
            # fixme: 返回对应的公钥指纹
            ("no public key"!=verify.status, 401, "服务器中没有公钥，通过pubkey接口上传公钥"),
            (verify.valid, "签名信息错误"),
            (verify.pubkey_fingerprint, '证书中uid最少指定名称，否则后端无法正确解析公钥指纹')
        )
        return verify.pubkey_fingerprint.upper(), int(verify.sig_timestamp)


def verify(require=True, auth_check=lambda f: True):
    def __inner_wrapper(func):
        spec = inspect.getfullargspec(func)
        @wraps(func)
        def __do_verify(*args, **kwargs):
            strsign = request.headers.get('Sign', '')
            fingerprint = ''
            if strsign:
                # 验证签名
                try:
                    strsign = json.loads(strsign)
                except:
                    return build_response(400, '签名信息有问题，必须使用json序列化')
                data = '{method} {path}'.format(method=request.method, path=request.full_path)
                if request.data:
                    data = data + '\r\n' + request.data.decode('utf-8')
                fingerprint, sig_ts = check_sign(strsign, data)
                assert_check(sig_ts+reply_timeout > time.time(), '签名过期，请重新签名后再请求')
                # 验证nonce
                check_nonce()
            # 如果要求签名，则必须进行身份验证
            if require:
                assert_check(
                    (''!=fingerprint, '接口要求签名'),
                    (auth_check(fingerprint), 401, '无权限，拒绝执行')
                )
            # 如果函数要求指纹数据，则传递指纹信息
            if spec.varkw or "fingerprint" in spec.args:
                kwargs.update(fingerprint=fingerprint)

            return func(*args, **kwargs)
        return __do_verify
    return __inner_wrapper


@pubkey.route("", methods=["PUT"])
def api_add():
    assert_check(request.json, '请以json格式提交pubkey')
    pubkey = str(request.json.get("pubkey", ""))
    assert_not_empty(pubkey=pubkey)

    begin = "-----BEGIN PGP PUBLIC KEY BLOCK-----"
    end = "-----END PGP PUBLIC KEY BLOCK-----"
    if begin not in pubkey:
        pubkey = begin + "\n" + pubkey
    if end not in pubkey:
        pubkey = pubkey + "\n" + end

    r = gpg.import_keys(pubkey)
    assert_check(len(r.fingerprints)>0, "pubkey格式有误，请确认无误后再上传")
    fingerprint = r.fingerprints[0].upper()

    return build_response(fingerprint=fingerprint, admin=admin_fingerprint==fingerprint)


@pubkey.route("/<string:fingerprint>", methods=["GET"])
def api_get(fingerprint):
    check_fingerprint_format(fingerprint)
    pubkey = gpg.export_keys(fingerprint)
    assert_check(pubkey, 404, '找不到指定的公钥信息')
    return build_response(pubkey=pubkey)


# @pubkey.route('/relationship', methods=['PUT'])
# @verify(require=True)
# def api_add_relationship(fingerprint):
#     '''
#         seed.json {
#             "relationship": "...",
#             "fingerprint": "..."
#         }
#     '''
#     j = request.json
#     try:
#         data = json.loads(j['json'])
#     except: 
#         return build_response(400, 'json字段解析失败')

#     check_fingerprint_format(data['fingerprint'])
#     assert_check(
#         data['relationship'] in pubkey_support_relationships,
#         'relationship目前仅支持'+','.join(pubkey_support_relationships)
#     )
#     fp, sig_ts = check_sign(j['sign'], j['json'])
#     assert_check(
#         (fp==fingerprint, '请求签名与携带数据签名不一致，拒绝执行'),
#         (data['fingerprint']!=fingerprint, '不能与自己建立关系，拒绝执行')
#     )

#     adpr.fp_relationship_create(
#         fingerprint,
#         data['fingerprint'],
#         data['relationship'],
#         sig_ts,
#         j
#     )
#     return build_response()


# @pubkey.route('/<string:relationship>/<string:target_fp>', methods=['DELETE'])
# @verify(require=True)
# def api_delete_relationship(relationship, target_fp, fingerprint):
#     check_fingerprint_format(target_fp)
#     assert_check(
#         relationship in pubkey_support_relationships, 
#         'relationship目前仅支持'+','.join(pubkey_support_relationships)
#     )

#     adpr.fp_relationship_delete(
#         fingerprint,
#         target_fp,
#         relationship
#     )
#     return build_response()


# @pubkey.route('/<string:from_fp>/<string:relationship>', methods=['GET'])
# def api_get_relationship(from_fp, relationship):
#     a = request.args
#     page = a.get('page', default=1, type=int)
#     page_size = a.get('page_size', default=20, type=int)

#     assert_check(
#         (isinstance(page, int) and page>0, 'page 参数必须为大于0的正整数'),
#         (isinstance(page_size, int) and 100>=page_size>0, 'page_size参数必须取值范围为1-100')
#     )

#     check_fingerprint_format(from_fp)
#     assert_check(
#         relationship in pubkey_support_relationships,
#         'relationship目前仅支持'+','.join(pubkey_support_relationships)
#     )

#     data = adpr.fp_relationship_list(from_fp, relationship, page, page_size)
#     return build_response(**data)

