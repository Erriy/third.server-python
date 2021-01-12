#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import re
from urllib.parse import urlparse, parse_qs


home = 'http://feijisu7.com/'
name = '飞极速在线'


class search:
    init = lambda key: api.request(
        url='/search/' + key,
    ).xml
    list = lambda h: h.xpath('//*[@id="result"]/li')
    info = lambda i: dict(
        name=''.join(i.xpath('h2/a/text()')),
        poster=''.join(i.xpath('a/img/@src')),
        epid=''.join(re.findall(r'/acg/(\d+)', ''.join(i.xpath('h2/a/@href')))),
        description=''.join(i.xpath('p/text()'))
    )


class episodes:
    init = lambda id: api.request('/acg/{}/'.format(id)).xml
    list = lambda h: h.xpath('//*[@id="qiyi-pl-list"]/div/ul/li')
    info = lambda i: dict(
        name=''.join(i.xpath('a/@title')).encode('ISO-8859-1').decode('utf-8'),
        vid=''.join(re.findall(r'(\d+).html', ''.join(i.xpath('a/@href'))))
    )


def video(epid, vid):
    h = api.request('/acg/{}/{}.html'.format(epid, vid)).xml
    return ''.join(parse_qs(urlparse(''.join(h.xpath('/html/body/iframe/@src'))).query)['vid'])

