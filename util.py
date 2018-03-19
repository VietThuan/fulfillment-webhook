from config import ChatbotConfig

cfg = ChatbotConfig()

token_hash = cfg.DFClientToken[0:4] + '***' + cfg.DFClientToken[-4:]


def get_sender_id(req):
    return req['originalRequest']['data']['sender']['id']


def hide_token(str):
    return str.replace(cfg.DFClientToken, token_hash)


def get_facebook_sender_id(req):
    # Chỉ xử lý câu trả lời cho hội thoại trên facebook
    if not is_contain_key("originalRequest;source", req, "facebook"):
        return None

    for item in req["result"]["contexts"]:
        try:
            return item["parameters"]["facebook_sender_id"]
        except:
            pass
    return None


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
