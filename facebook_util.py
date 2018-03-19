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
cache = TTLCache(maxsize=int(cfg.CacheMaxsize), ttl=int(cfg.CacheTTL))
lock = RLock()


@cached(cache, lock=lock)
def get_facebook_sender_id(id):
    """
    Lấy thông tin của Facebook theo senderID
    :param id: facebook sender id
    :return:
    """
    response = ''
    try:
        logging.debug("Get Facebook info id[{}]".format(id))
        fields = 'first_name,last_name,gender'
        conn = http.client.HTTPSConnection("graph.facebook.com")
        conn.request("GET", "/v2.11/{}?fields={}&access_token={}".format(id, fields, cfg.FanpageToken))

        res = conn.getresponse()
        data = res.read()
        response = data.decode("utf-8")

        obj = json.loads(response)
        return obj
    except Exception as ex:
        logging.error("Error one get_facebook_sender_id, id[{}] response[{}] traceback[{}]"
                      .format(id, response, traceback.format_exc()))
        raise ex


def is_conversation_in_inbox(sender_id):
    response = ''
    try:
        print("Check conversation in inbox sender_id[{}]".format(sender_id))
        conn = http.client.HTTPSConnection("graph.facebook.com")
        conn.request("GET", "/v2.12/{}/conversations?access_token={}".format(sender_id, cfg.FanpageToken))

        res = conn.getresponse()
        data = res.read()
        response = data.decode("utf-8")
        obj = json.loads(response)
        return len(obj['data']) > 0
    except Exception:
        logging.error("Error one get_info, sender_id[{}] response[{}] traceback[{}]".format(sender_id, response,
                                                                                            traceback.format_exc()))
        return False


with lock:
    cache.clear()


# Tạo tên xưng hô từ giới tính lấy được từ Facebook
def make_viet_name_gender(value, is_upper):
    if value == "male":
        if is_upper:
            return "Anh"
        else:
            return "anh"
    elif value == "female":
        if is_upper:
            return "Chị"
        else:
            return "chị"
    return "Anh/Chị"
