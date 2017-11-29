# Luu cache trong 30 phut
import http
import json

from cachetools import TTLCache, cached

from config import ChatbotConfig

cfg = ChatbotConfig()
from threading import RLock

cache = TTLCache(maxsize=100, ttl=1800)
lock = RLock()


# Kiểm tra key có tồn tại trong dic hay không
def isContainKey(data, dic, value):
    datas = data.split(";")
    for item in datas:
        if item not in dic:
            return False
        else:
            dic = dic.get(item)
    if value != "" and value != dic:
        return False
    return True


# @lru_cache_function(max_size=1024, expiration=30 * 60)
@cached(cache, lock=lock)
def get_info(id):
    print("Get Facebook info {}".format(id))
    fields = 'first_name,last_name,profile_pic,locale,timezone,gender'
    conn = http.client.HTTPSConnection("graph.facebook.com")
    conn.request("GET", "/v2.11/{}?fields={}&access_token={}".format(id, fields, cfg.FANPAGE_TOKEN))

    res = conn.getresponse()
    data = res.read()

    obj = json.loads(data.decode("utf-8"))
    return obj


with lock:
    cache.clear()


def makeVietNameGender(value, isUpper):
    if value == "male":
        if isUpper == True:
            return "Anh"
        else:
            return "anh"
    elif value == "female":
        if isUpper == True:
            return "Chị"
        else:
            return "chị"
    return "Anh/Chị"
