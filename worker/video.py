#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import cv2
import picture


def thumbnail(src, dst, frames=16, size='small', quality=100):
    v = cv2.VideoCapture(src)
    success, frame = v.read()
    success, buffer = cv2.imencode('.jpg', frame)
    picture.thumbnail(buffer, dst, size=size, quality=quality)



if __name__ == "__main__":
    src = '/home/erriy/test/IMG_2724_HEVC.MOV'
    dst = 'test.jpg'
    thumbnail(src, dst)









