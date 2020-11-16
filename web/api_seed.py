#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import json
import hashlib
import time
import string
from flask import Blueprint, request
from api_pubkey import verify, check_sign
from web_common import build_response, assert_check, adpr, pubkey_support_relationships


seed = Blueprint("seed", __name__)


allow_char_set = set(string.ascii_letters+string.digits+'_-.')
def check_seedid(seedid):
    assert_check(
        (len(seedid)>20, 'seedid非法，拒绝执行'),
        (not (set(str(seedid)) - allow_char_set), 'seedid 包含非法字符，拒绝执行')
    )


@seed.route('', methods=['PUT'])
@verify(require=True)
def api_create(fingerprint):
    # todo 创建与更新拆分成不同接口，可能因为id冲突而导致意外更新其他节点（冲突概率极低，但是依然可能会发生，所以不能忽视）
    # 唯一性id不能使用短id，否则不同用户创建的不同数据可能会相同，必须足够随机
    # fork自其他人的数据，应该有个引用id，使用全id，uuid_fingerprint_sha256_timestamp
    try:
        j = request.json
    except:
        return build_response('提交的数据格式有误，仅支持json格式')
    # 只有当public明确指定为true时才为公开数据。请求未签名时提交的数据也是这样
    # 也就是说如果你的私有数据被别人拿走了，然后重新提交，会造成私有数据公开化。所以私有数据并不能完全保证私有，特别重要的信息需要自建服务器或进行加密处理
    public = str(request.args.get('public', 'false')).lower() == 'true'
    # 支持单个seed
    if not isinstance(j, list):
        j = [j]

    formated_seed_list = []
    for seed in j:
        # 校验格式
        assert_check(isinstance(seed, dict), 'seed必须为字典')
        json_seed = seed['json']
        sign_list = seed['sign']
        assert_check(
            isinstance(sign_list, list) and len(sign_list) > 0,
            'seed中的签名信息格式不正确，必须为至少包含一个签名的列表'
        )
        # 校验签名并保存签名的值
        seed['sign_fingerprint'] = []
        for sign in sign_list:
            fp, sig_ts = check_sign(sign, json_seed)
            seed['sign_fingerprint'].append(fp)
        # 判断json数据是否合法，并反序列化出object_seed
        try:
            object_seed = json.loads(json_seed)
            seed['object'] = object_seed
        except json.decoder.JSONDecodeError:
            return build_response(400, "json数据不合法")
        # 提取update_ts信息
        assert_check(
            'metadata' in object_seed and isinstance(object_seed['metadata'], dict),
            400, 'seed数据未包含元信息或格式不正确'
        )
        metadata = object_seed['metadata']
        assert_check(
            'time' in metadata and isinstance(metadata['time'], dict),
            400, 'seed元数据中未包含时间信息或格式不正确'
        )
        meta_time = metadata['time']
        assert_check(
            'update' in meta_time and isinstance(meta_time['update'], dict),
            400, 'seed元数据时间信息中未包含更新时间或格式不正确'
        )
        meta_update = meta_time['update']
        assert_check(
            'timestamp' in meta_update and isinstance(meta_update['timestamp'], (float, int)),
            400, 'seed元数据时间信息中更新时间未包含时间戳或格式不正确'
        )
        update_ts = meta_update['timestamp']
        # assert_check(update_ts<=time.time(), 400, '不接受来自未来的信息，请确认时间准确后再提交')
        # seedid 是否存在
        seedid = metadata.get("id", {}).get("value")
        assert_check(isinstance(seedid, str) and len(seedid) > 20, 'id不存在或不合法')
        # 判断签名是否正常
        author_list = metadata.get("author", [])
        assert_check(isinstance(author_list, list) and len(author_list) > 0, 400, '必须指定作者信息')
        author_list = [str(author).upper() for author in author_list]
        assert_check(not (set(author_list) - set(seed['sign_fingerprint'])), 400, '有作者未签名，拒绝接受本信息')
        # 检查关系名和链接id
        for l in metadata.get('link', []):
            check_seedid(l['id'])
        # 计算sha256
        sha256 = hashlib.sha256(json_seed.encode('utf-8')).hexdigest().upper()
        # 计算id
        author_list.sort()
        seed['seedid'] = seedid
        seed['seedid_owner'] = seedid + "-" + '.'.join(author_list)
        seed['seedid_full'] = seed['seedid'] + '-' + sha256 + '-' + str(update_ts)

        formated_seed_list.append(seed)

    for seed in formated_seed_list:
        adpr.seed_create(fingerprint, public, seed)
    return build_response()


@seed.route('/<string:seedid>', methods=['DELETE'])
@verify(require=True)
def api_delete(seedid, fingerprint):
    pass


@seed.route('', methods=['GET'])
@verify(require=True)
def api_search(fingerprint):
    a = request.args

    key = a.get('key', default='', type=str)
    zone = a.get('zone', default='', type=str)
    depth = a.get('depth', default=1, type=int)
    page = a.get('page', default=1, type=int)
    page_size = a.get('page_size', default=20, type=int)
    from_ts = a.get('from', default=-1, type=float)
    to_ts = a.get('to', default=-1, type=float)
    link = a.get('link', default='', type=str)
    link = list(map(lambda x: x.split(":"),filter(lambda x: x,link.split(','))))

    for l in link:
        check_seedid(l[0])

    zone_list = [''] + pubkey_support_relationships
    assert_check(
        (zone in zone_list, '不支持的zone, 可选值为' + ','.join(zone_list)),
        (0<=depth<=4, 'depth取值范围为0-4(按四/六度分隔理论，4层已经几乎信任所有人了)'),
        (isinstance(page, int) and page>0, 'page 参数必须为大于0的正整数'),
        (isinstance(page_size, int) and 100>=page_size>0, 'page_size参数必须取值范围为1-100')
    )
    sl = adpr.seed_search(
        key=key,
        fp=fingerprint,
        zone=zone,
        depth=depth,
        page=page,
        page_size=page_size,
        link=link,
        from_ts=from_ts,
        to_ts=to_ts,
    )
    return build_response(list=sl)


@seed.route("/<string:seedid>", methods=['GET'])
@verify(require=True)
def api_info(seedid, fingerprint):
    check_seedid(seedid)
    data = adpr.seed_info(fingerprint, seedid)
    if data:
        return build_response(**data)
    else:
        return build_response(404, '未找到资源')


@seed.route('/<string:seedid>/version', methods=['GET'])
@verify(require=True)
def api_version(seedid, fingerprint):
    check_seedid(seedid)
    a = request.args
    page = a.get('page', default=1, type=int)
    page_size = a.get('page_size', default=20, type=int)
    assert_check(
        (isinstance(page, int) and page>0, 'page 参数必须为大于0的正整数'),
        (isinstance(page_size, int) and 100>=page_size>0, 'page_size参数必须取值范围为1-100')
    )
    list = adpr.seed_version(fingerprint, seedid, page, page_size)
    return build_response(list=list)

