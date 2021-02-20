# -*- coding: UTF-8 -*- #
from random import random

import requests
import base64
import cv2
import json

def detect_person_reid(info, url):
    """
        Args:
            info: dict of a frame {'img':im, 'frame_num':int}
            url: string of server
    """
    frame_num = info['frame_num']
    img_opencv = info['img']

    succ = False
    while not succ:
        try:
            succ, base64_str = cv2.imencode('.jpg', img_opencv)
        except IOError:
            print("Transfer Error incurred in frame {}. Will redo. Don't worry. Just chill.".format(frame_num))
            pass

    file = base64.b64encode(base64_str)
    files = {'img': file, 'frame_num': frame_num}

    # 获取服务器返回的图片，字节流返回
    r = requests.post(url, files=files)
    result = r.content
    result = json.loads(s=result)
    print(result)

    return result['info'], result['people'], result['frame_num']

# Plotting functions ---------------------------------------------------------------------------------------------------
def plot_one_box(x, img, color=None, label=None, line_thickness=None):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1)  # filled
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [0, 0, 0], thickness=tf, lineType=cv2.LINE_AA)7


if __name__ == '__main__':

    url = "http://www.wujiacloud.top:6060/photo"
    # url = "http://127.0.0.1:12345/photo"

    mot = r'video_frames'
    from glob import glob
    import os
    img_lists = glob(os.path.join(mot, '*.jpg'))
    fps = 0.0
    for idx, img_p in enumerate(img_lists):
        frame = cv2.imread(img_p)
        info = {'img': frame, 'frame_num': idx}
        succ, people, _ = detect_person_reid(info, url)

        if people:
            for p in people:
                plot_one_box(p['pos'], frame, label=str(p['person_id']), color=[255, 255, 0])
        cv2.imshow('person search', frame)
        cv2.waitKey(1)

    r = requests.post("http://www.wujiacloud.top:6060/ping")
    print(r.content)

    r = requests.post("http://www.wujiacloud.top:6060/reinit_mot")
    print(r.content)
