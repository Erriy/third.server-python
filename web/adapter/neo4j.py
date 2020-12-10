#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import json
from urllib.parse import quote,unquote
from .base import adapter as base_adapter
from py2neo import Graph


class adapter(base_adapter):
    def __init__(self, host, port, user, password):
        self.__host = host
        self.__port = port
        self.__user = user
        self.__password = password

        self.__graph = Graph(
            host=self.__host,
            port=self.__port,
            auth=(self.__user, self.__password)
        )

        try:
            self.__graph.run("create constraint on (n:fp) assert n.`fingerprint` is unique")
        except:
            pass
        try:
            self.__graph.run("create constraint on (n:seed) assert n.`seedid` is unique")
        except:
            pass
        try:
            self.__graph.run("create constraint on (n:history) assert n.`seedid_full` is unique")
        except:
            pass

    def __dumps(self, obj):
        return quote(json.dumps(obj, separators=[',', ':'], ensure_ascii=False))

    def __loads(self, data):
        return json.loads(unquote(data))

    def fp_relationship_create(self, from_fp, to_fp, relationship, timestamp, seed):
        cql = '''
            merge (_from:fp{{fingerprint: '{from_fp}'}}) with _from
            merge (_to:fp{{fingerprint: '{to_fp}'}}) with _from, _to
            merge (_from)-[r:{relationship}]->(_to)
                on create set r.timestamp={timestamp}, r.seed='{seed}'
        '''.format(
            from_fp=from_fp,
            to_fp=to_fp,
            relationship=relationship,
            timestamp=timestamp,
            seed=self.__dumps(seed)
        )
        self.__graph.run(cql)

    def fp_relationship_delete(self, from_fp, to_fp, relationship):
        cql = '''
            match (_from:fp)-[r:{relationship}]->(_to:fp)
                where _from.fingerprint='{from_fp}'
                    and _to.fingerprint='{to_fp}'
            delete r
        '''.format(
            from_fp=from_fp,
            to_fp=to_fp,
            relationship=relationship
        )
        self.__graph.run(cql)

    def fp_relationship_list(self, fp, relationship, page, page_size):
        cql = '''
            match (_fp:fp)-[r:{relationship}]->(:fp)
                where _fp.fingerprint='{fingerprint}'
            with distinct r order by r.timestamp desc
            return r skip {skip} limit {page_size}
        '''.format(
            relationship=relationship,
            fingerprint=fp,
            skip=(page-1)*page_size,
            page_size=page_size,
        )
        data = dict(list=[])
        for r, in self.__graph.run(cql):
            data['list'].append(self.__loads(r.get('seed')))
        return data

    def seed_create(self, fp, public, seed):
        oseed = seed['object']
        # 创建节点
        set_string = '''
            n.seedid='{seedid_owner}',
            n.seedid_full='{seedid_full}',
            n.update_ts={update_ts},
            n.public='{public}',
            n.seed='{seed}'
        '''.format(
            seedid_owner=seed['seedid_owner'],
            seedid_full=seed['seedid_full'],
            update_ts=oseed['metadata']['time']['update']['timestamp'],
            public=public,
            seed=self.__dumps(dict(json=seed['json'], sign=seed['sign'], public=public))
        )

        # fixme: 旧数据重新上传导致旧数据重新覆盖
        # 建立节点并删除相关关系
        cql_seed = '''
            merge (n:seed{{seedid: '{seedid_owner}'}})
                on create set {set_string}
            with n
            merge (owner:fp{{fingerprint: '{fingerprint}'}}) with owner,n
            merge (owner)-[r:own]->(n) with n
            merge (v:seed{{seedid:'{seedid}'}}) with v, n
            merge (v)-[:version]->(n)
            with n where n.seedid_full<>'{seedid_full}'
                create (h:history)-[:history]->(n)
                    set h=n, {set_string}
            with n match (n)-[r:link]->() delete r
        '''.format(
            seedid=seed['seedid'],
            seedid_owner=seed['seedid_owner'],
            seedid_full=seed['seedid_full'],
            set_string=set_string,
            fingerprint=fp,
        )
        self.__graph.run(cql_seed)

        # 连接相关节点
        _ = []
        for i in oseed['metadata'].get('link', []):
            _.append('''
                with distinct n merge (n1:seed{{seedid:'{target_seedid}'}}) with n, n1
                    create (n)-[:link{{name:'{rname}'}}]->(n1)
                '''.format(
                    target_seedid=i['id'],
                    rname=quote(i['name'])
            ))
        if _:
            cql_link = '''
                match (n:seed) where n.seedid='{seedid_owner}'
                {links}
            '''.format(
                seedid_owner=seed['seedid_owner'],
                links=''.join(_)
            )
            self.__graph.run(cql_link)

    def seed_delete(self, fp, seedid):
        cql = '''
            match (s)<-[:history*0..]-(n) where s.`seedid`='{seedid}' detach delete n
        '''.format(
            seedid=seedid+'-'+fp
        )
        self.__graph.run(cql)

    def seed_search(self, fp, link, key, zone, depth, from_ts, to_ts, page, page_size):
        # todo: 支持全文检索，增加过滤条件
        key_filter = ''
        if key:
            key_filter = " where n.seed=~'(?ms).*%s.*' "%(quote(key))

        ts_filter = ''
        if 0 < from_ts:
            ts_filter += ' and n.update_ts>%s '%(from_ts)
        if 0 < to_ts:
            ts_filter += ' and n.update_ts<%s '%(to_ts)

        link_filter = ''
        if link:
            for l in link:
                seedid, *name = l
                link_filter += ' where (n)-[:link{{{prop}}}]->(:seed{{seedid:"{seedid}"}}) or (n)-[:link{{{prop}}}]->()-[:version]-(:seed{{seedid:"{seedid}"}})'.format(
                    prop='name: "%s"'%(quote(name[0])) if name else '',
                    seedid=seedid
                )
        zone_filter = ''
        if zone:
            zone_filter = '(f)-[:{zone}*0..{depth}]->()-[:own]->(n) and '.format(zone=zone, depth=depth)
        cql = '''
            merge (f:fp{{fingerprint: '{fingerprint}'}}) with f
            match (n:seed) where (({zone_filter} n.public='True') or (f)-[:own]->(n)) {ts_filter}
            with n,f {link_filter}
            with n,f {key_filter}
            with f, count(n) as total
            match (n:seed) where (({zone_filter} n.public='True') or (f)-[:own]->(n)) {ts_filter}
            with n,f,total {link_filter}
            with n,f,total {key_filter}
            return distinct n, total order by n.`{sort}` desc skip {skip} limit {page_size}
        '''.format(
            depth=depth,
            fingerprint=fp,
            zone_filter=zone_filter,
            sort='update_ts',
            skip=(page-1)*page_size,
            page_size=page_size,
            link_filter=link_filter,
            key_filter=key_filter,
            ts_filter=ts_filter,
        )
        data = dict(list=[], total=0)

        for n,total in self.__graph.run(cql):
            data['total'] = total
            data['list'].append(self.__loads(n['seed']))

        return data

    def seed_info(self, fp, seedid):
        cql = '''
            merge (f:fp{{fingerprint: '{fingerprint}'}}) with f
            match (n:seed)
                where n.seedid='{seedid}'
                    and (n.public='True' or (f)-[:own]->(n))
            return distinct n
        '''.format(
            fingerprint=fp,
            seedid=seedid
        )
        seed = None
        for n, in self.__graph.run(cql):
            seed = self.__loads(n['seed'])

        if not seed:
            return None

        cql = '''
            match (n:seed)-[:version*0..2]-()<-[r:link]-() where n.seedid='{seedid}'
            return distinct r.name as rname
        '''.format(seedid=seedid)
        link = []
        for rname, in self.__graph.run(cql):
            link.append(unquote(rname))
        return dict(seed=seed, link=link)

    def seed_version(self, fp, seedid, page, page_size):
        cql = '''
            merge (f:fp{{fingerprint: '{fingerprint}'}}) with f
            match (s:seed) where s.seedid='{seedid}' with s,f
            match (s)<-[:version*0..1]-()-[:version]->(n:seed)
            return distinct n order by n.`{sort}` desc skip {skip} limit {page_size}
        '''.format(
            fingerprint=fp,
            seedid=seedid,
            sort='update_ts',
            skip=(page-1)*page_size,
            page_size=page_size,
        )
        seed_list = []
        for n, in self.__graph.run(cql):
            seed_list.append(self.__loads(n['seed']))
        return seed_list
