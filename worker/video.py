#!/usr/bin/env python3
# -*- coding=utf-8 -*-
import cv2
import picture


def thumbnail(src, dst, frames=16, size='small', quality=100):
    cap = cv2.VideoCapture(src)
    all_frames = cap.get(7)
    frames = frames if all_frames > frames else all_frames
    gap = int(all_frames/frames)
    for i in range(frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i*gap)
        is_success, frame = cap.read()
        is_success, buffer = cv2.imencode('.jpg', frame)
        picture.thumbnail(buffer, '%s_%d.jpg'%(dst, i), size=size, quality=quality)


if __name__ == "__main__":
    src = '/home/erriy/test/test.mov'
    dst = 'test'
    import time
    s = time.time()
    thumbnail(src, dst, 22, 'large', quality=70)
    print('耗时', time.time() - s)









