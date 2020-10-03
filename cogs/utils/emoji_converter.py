import re


class EmojiConverter:
    def __init__(self):
        import requests
        import re
        self.data = requests.get(
            'https://unicode.org/emoji/charts/full-emoji-list.html').text

    def to_base64_png(self, emoji, version=0):
        """For different versions, you can set version = 0 for , """
        html_search_string = r"<img alt='{}' class='imga' src='data:image/png;base64,([^']+)'>"  # '
        matchlist = re.findall(html_search_string.format(emoji), self.data)
        return matchlist[version]
