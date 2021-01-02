#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import pyheif
from PIL import Image


def thumbnail(src, dst, size='small', quality=100):
    '''
        制作缩略图
        - src：源文件路径
        - dst：生成的缩略图路径
        - size： 'small','middle', 'large'
        - quality：质量
    '''
    if 'small' == size:
        max_length = 100
    elif 'middle' == size:
        max_length = 300
    elif 'large' == size:
        max_length = 800
    else:
        raise 'size[%s]参数不正确'%(str(size))

    ext = src.split('.')[-1].lower()
    if 'heic' == ext:
        with open(src, 'rb') as f:
            data = f.read()
        i = pyheif.read_heif(data)
        im = Image.frombytes(mode=i.mode, size=i.size, data=i.data)
    else:
        im = Image.open(src)

    width, height = im.size

    if width >= max_length and height >= max_length:
        wscale = max_length / width
        hscale = max_length / height
        scale = wscale if wscale > hscale else hscale
        width = int(scale*width)
        height = int(scale*height)

    im.resize((width, height), Image.ANTIALIAS).save(dst, quality=quality)


if __name__ == "__main__":
    src = '/home/erriy/test/IMG_3733.HEIC.jpg'
    dst = 'test.jpg'
    for i in ['small', 'middle', 'large']:
        thumbnail(src, i+dst, i, 70)

