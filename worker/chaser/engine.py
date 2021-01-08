#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import os
import importlib.util
import requests
import json
import youtube_dl
from urllib.parse import urljoin
from lxml import etree
from inspect import isfunction, isclass, signature


class _data:
    def __init__(self, code=None, headers={}, text=''):
        self.__code = code
        self.__headers = headers
        self.__text = text
        self.__json = None
        self.__xml = None

    @property
    def json(self):
        if not self.__json:
            self.__json = json.load(self.__text)
        return self.__json

    @property
    def xml(self):
        if not self.__xml:
            self.__xml = etree.HTML(self.__text)
        return self.__xml

    @property
    def text(self):
        return self.__text

    @property
    def code(self):
        return self.__code

    @property
    def headers(self):
        return self.__headers


class attr_dict(dict):
    def __init__(self, *args, **kwargs):
        super(attr_dict, self).__init__(*args, **kwargs)
        self.__dict__ = self


class chaser:
    def __init__(self, rule_module):
        self.__obj = rule_module
        self.__headers = {
            'Referer': self.home,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        }
        self.__obj.api = attr_dict(
            request=self.__request,
        )
        self.search = self.__generate_list_handler('search')
        self.episodes = self.__generate_list_handler('episodes')
        self.video = self.__obj.video

    @property
    def home(self):
        return self.__obj.home

    @property
    def rule(self):
        return self.__obj.__name__

    @property
    def name(self):
        return getattr(self.__mobj, 'name', self.rule)

    def __request(self, url='', method='GET', headers={}, **kwargs):
        new_header = dict(**self.__headers)
        new_header.update(**headers)
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 60
        r = requests.request(
            method=method.upper(),
            url=urljoin(self.home, url),
            headers=new_header,
            **kwargs
        )
        return _data(code=r.status_code, headers=r.headers, text=r.text)

    def __generate_list_handler(self, handler_name):
        handler = getattr(self.__obj, handler_name, None)
        assert handler, '%s 不存在'%(handler_name)

        if isfunction(handler):
            return handler
        elif isclass(handler):
            ins = handler()

            def get_function(name):
                func = getattr(handler, name, None)
                assert func, '{hn}.{mn} 不存在'.format(hn=handler_name, mn=name)
                sp = signature(func).parameters
                return getattr(ins, name) if len(sp) > 0 and list(sp)[0] == 'self' else func
            _init = get_function('init')
            _list = get_function('list')
            _info = get_function('info')
            def __real_do_list(*args, **kwargs):
                return list(map(
                    lambda *args, **kwargs: dict(rule=self.rule, **_info(*args, **kwargs)),
                    _list(_init(*args, **kwargs))
                ))
            return __real_do_list
        else:
            raise '%s 为不支持的类型'%(handler_name)


def load(dirname):
    pwd = os.path.dirname(os.path.abspath(__file__))
    dirpath = os.path.join(pwd, dirname)

    mobj_dict = dict()

    for filename in filter(lambda f: f.lower().endswith('.py'), os.listdir(dirpath)):
        filepath = os.path.join(dirpath, filename)
        module_name = filename[:-3]
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        mobj = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mobj)
        mobj_dict[module_name] = chaser(mobj)

    return mobj_dict


chasers = load('rules')


def download(url, path, cb):
    ydl_opts = dict(outtmpl=path, progress_hooks=[cb], quiet=True)
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


'''

input





output




返回基本信息
dict(
    engine='',
    name='',
    home='',
)

返回list结果
dict(
    engine='',
    list=[],
    page=int,
    next_page=int,
)

返回单一结果
dict(
    engine='',
    name='',
    result=anything,
)
'''











