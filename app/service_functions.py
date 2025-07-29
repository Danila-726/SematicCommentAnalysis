import re

def validate_url(url: str) -> bool:
    vk_pattern = r'^https://vkvideo\.ru/video-\d+_\d+$'
    rutube_pattern = r'^https://rutube\.ru/video/[a-fA-F0-9]{32}/?$'

    return bool(re.fullmatch(vk_pattern, url) or bool(re.fullmatch(rutube_pattern, url)))

def is_url_rutube(url):
    rutube_pattern = r'^https://rutube\.ru/video/[a-fA-F0-9]{32}/?$'

    if bool(re.fullmatch(rutube_pattern, url)): return True
    return False

