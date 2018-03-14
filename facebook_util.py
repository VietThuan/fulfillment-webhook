# Luu cache trong 30 phut
import http
import http.client
import json
import logging
import traceback
from threading import RLock

from cachetools import TTLCache, cached

from config import ChatbotConfig

cfg = ChatbotConfig()

# Tạo cache
cache = TTLCache(maxsize=int(cfg.CACHE_MAXSIZE), ttl=int(cfg.CACHE_TTL))
lock = RLock()


# Kiểm tra key có tồn tại trong dic hay không
def is_contain_key(data, dic, value):
    datas = data.split(";")
    for item in datas:
        if item not in dic:
            return False
        else:
            dic = dic.get(item)
    if value != "" and value != dic:
        return False
    return True


# Lấy thông tin của Facebook theo senderID
@cached(cache, lock=lock)
def get_info(id):
    try:
        print("Get Facebook info {}".format(id))
        fields = 'first_name,last_name,gender'
        conn = http.client.HTTPSConnection("graph.facebook.com")
        conn.request("GET", "/v2.11/{}?fields={}&access_token={}".format(id, fields, cfg.FANPAGE_TOKEN))

        res = conn.getresponse()
        data = res.read()

        obj = json.loads(data.decode("utf-8"))
        return obj
    except Exception as ex:
        logging.error("Error one get_info:" + traceback.format_exc())
        raise ex


def is_conversation_in_inbox(sender_id):
    try:
        print("Check conversation in inbox sender_id[{}]".format(sender_id))
        conn = http.client.HTTPSConnection("graph.facebook.com")
        conn.request("GET", "/v2.12/{}/conversations?access_token={}".format(sender_id, cfg.FANPAGE_TOKEN))

        res = conn.getresponse()
        data = res.read()

        obj = json.loads(data.decode("utf-8"))
        return len(obj['data']) > 0
    except Exception as ex:
        logging.error("Error one get_info:" + traceback.format_exc())
        return False


with lock:
    cache.clear()


# Tạo tên xưng hô từ giới tính lấy được từ Facebook
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
