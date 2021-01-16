#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import json
import time
from flask import Blueprint, request
from web_common import build_response, assert_check, neo4j, dumps, loads


seed = Blueprint("seed", __name__)


@seed.route('', methods=['PUT'])
def api_create():
    seed = request.json

    set_string = '''
        n.seedid='{seedid}',
        n.update_ts={update_ts},
        n.seed='{seed}'
    '''.format(
        seedid=seed['meta']['id'],
        seed=dumps(seed),
        update_ts=seed['meta']['time']['update']['timestamp']
    )

    cql_seed = '''
        merge (n:seed{{seedid: '{seedid}'}}) set {set_string}
    '''.format(
        seedid=seed['meta']['id'],
        set_string=set_string
    )

    neo4j.run(cql_seed)
    return build_response()


@seed.route('', methods=['GET'])
def api_search():
    a = request.args
    key = a.get('key', default='', type=str)
    page = a.get('page', default=1, type=int)
    page_size = a.get('page_size', default=20, type=int)
    from_ts = a.get('from', default=-1, type=float)
    to_ts = a.get('to', default=-1, type=float)

    assert_check(
        (isinstance(page, int) and page>0, 'page 参数必须为大于0的正整数'),
        (isinstance(page_size, int) and 100>=page_size>0, 'page_size参数必须取值范围为1-100')
    )

    swhere = ''
    search_filter = []

    # todo: 支持全文检索，增加过滤条件
    if key:
        search_filter.append(" n.seed=~'(?ms).*%s.*' "%(quote(key)))
    if 0 < from_ts:
        search_filter.append(' n.update_ts>{} '.format(from_ts))
    if 0 < to_ts:
        search_filter.append(' n.update_ts<{} '.format(to_ts))

    if search_filter:
        swhere = ' where ' + ' and '.join(search_filter)

    cql = '''
        match (n:seed) {swhere}
        with count(n) as total
        match (n:seed) {swhere}
        return distinct n, total order by n.`{sort}` desc skip {skip} limit {page_size}
    '''.format(
        swhere=swhere,
        sort='update_ts',
        skip=(page-1)*page_size,
        page_size=page_size
    )

    data = dict(list=[], total=0)
    for n,total in neo4j.run(cql):
        data['total'] = total
        data['list'].append(loads(n['seed']))

    return build_response(**data)


@seed.route('<string:seedid>', methods=['DELETE'])
def api_delete(seedid):
    cql = '''
        match (n:seed) where n.seedid='{seedid}' detach delete n
    '''.format(
        seedid=seedid
    )
    neo4j.run(cql)
    return build_response()

