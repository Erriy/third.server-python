#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import re
from urllib.parse import urlparse, parse_qs


home = 'http://www.kakadm.com/'
name = '卡卡动漫'


class search:
    init = lambda key: api.request(
        method='POST',
        url='/e/search/index.php',
        data=dict(
            show='title,ftitle,zz',
            tbname='movie',
            tempid=1,
            keyboard=key
        )
    ).xml
    list = lambda h: h.xpath('/html/body/div[4]/div[2]/div[1]/ul/li')
    info = lambda i: dict(
        name=''.join(i.xpath('h2/a/@title')),
        poster=''.join(i.xpath('a/img/@src')),
        epid=''.join(re.findall(r'\d+', ''.join(i.xpath('h2/a/@href')))),
        description=''.join(i.xpath('p/text()'))
    )


class episodes:
    init = lambda id: api.request('/anime/{}/'.format(id)).xml
    list = lambda h: h.xpath('//*[@id="main0"]/div/ul/li')
    info = lambda i: dict(
        name=''.join(i.xpath('a/text()')),
        vid=''.join(re.findall(r'/anime/\d+/(\d+)/', ''.join(i.xpath('a/@href'))))
    )


def video(epid, vid):
    h = api.request('/e/action/player_i.php?id={}&pid={}'.format(epid, vid)).xml
    return ''.join(parse_qs(urlparse(''.join(h.xpath('/html/body/iframe/@src'))).query)['vid'])

