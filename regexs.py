from re import finditer


class RegEx:

    def __init__(self, regex):
        self.regex = regex

    def get_group(self, link: str, group: int):
        for match in finditer(self.regex, link):
            return match.group(group)

        return None


PLAYLIST_LINK_REGEX = RegEx(r'(?:https:\/\/|)smashup\.ru\/share\/playlist\?id=(\d+)(?:&sharedBy=.{0,}|)')

