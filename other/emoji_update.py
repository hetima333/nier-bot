import json
import re
import requests
import io
import base64
import emoji

from pathlib import Path
from PIL import Image

data = requests.get(
    'https://unicode.org/emoji/charts/full-emoji-list.html').text

html_search_string = re.compile(r"<img alt='(.)' class='imga' src='data:image/png;base64,([^']+)'>")

matchlist = re.findall(html_search_string, data)

d = dict()

count = 0
prev = ''
for v in matchlist:
    if prev == v[0][0]:
        count += 1
    else:
        count = 0

    if count == 4:
        d[v[0]] = v[1]

    prev = v[0]

for k, v in d.items():
    data = io.BytesIO(base64.b64decode(v))
    emoji_img = Image.open(data).convert('RGBA').resize((20, 20), Image.BICUBIC)
    emoji_str = emoji.demojize(k)[1:-1]
    # print(emoji_str)
    try:
        emoji_img.save(f'data/img/emoji/{emoji_str}.png')
    except Exception:
        print(1)
        # emoji_img.save(f'data/img/emoji/a.png')

