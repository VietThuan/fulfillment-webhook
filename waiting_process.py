import logging
import threading

import time

import requests
from flask import jsonify

from config import ChatbotConfig
from enums import getMsgType
from facebook_messager_builder import MessageFactory
from facebook_util import get_info, makeVietNameGender, isContainKey

cfg = ChatbotConfig()

# Lớp gửi câu trả lời cho Facebook
class SendMessageTask:
    def __init__(self, generate_message_task, senderId):
        self.subject = generate_message_task
        self.senderId = senderId

    def run(self):
        # Tạo thread xử lý câu trả lời cho Facebook (cập nhật danh xưng và tên cho câu trả lời)
        create_response_thread = threading.Thread(target=self.execute, args=())
        create_response_thread.start()

        create_response_thread.join(timeout=int(cfg.THREAD_TIMEOUT))
        # Nếu quá thời gian mà thead vẫn chưa xong thì thực hiện gửi tin thông báo chờ đợi
        if create_response_thread.is_alive():

            # Tạo thread thực hiện trả lời nốt cho Facebook
            send_thread = threading.Thread(target=self.send_message, args=(create_response_thread,))
            send_thread.start()
            return jsonify({
                "speech": "Chờ em một chút nhé...",
                "displayText": "Chờ em một chút nhé...",
                "source": "MISA-webhook"
            })
        else:
            return jsonify(self.subject.result)

    # Gửi tin nhắn cho người chat theo senderID
    def send_message(self, thread):
        # Chờ đợi cho tới khi thread xử lý câu trả lời cho Facebook xong
        thread.join()
        logging.debug("Send to facebook id {}".format(self.senderId))

        # Lấy kết quả của thread đó để gửi cho người chat.
        for item in self.subject.result['messages']:
            # dataJSON = genDataJSON(sender_id, item)
            if not isContainKey("platform", item,'facebook'):
                continue
            dataJSON = MessageFactory().create_message(item['type'], self.senderId, item)
            res = requests.post(
                "https://graph.facebook.com/v2.11/me/messages",
                params={"access_token": cfg.FANPAGE_TOKEN},
                headers={"Content-Type": "application/json"},
                data=dataJSON
            )
            logging.debug("Send result: {}".format(str(res)))

    def execute(self):
        self.subject.run()

# Tạo câu trả lời cho Facebook
class GetGenderTask:
    def __init__(self, req, senderId):
        self.senderId = senderId
        self.req = req

    def run(self):
        if self.senderId != "":
            if self.req['result']['resolvedQuery'].lower() == "facebook_welcome" or self.req['result'][
                'resolvedQuery'].lower() == "welcome":
                get_info(self.senderId)
            genderL = makeVietNameGender(get_info(self.senderId).get("gender"), False)
            genderU = makeVietNameGender(get_info(self.senderId).get("gender"), True)
            facebookName = get_info(self.senderId).get("first_name") + " " + get_info(self.senderId).get("last_name")
            arrGengerU = cfg.GENDER_U.split(";")
            arrGengerL = cfg.GENDER_L.split(";")

            for item in self.req['result']['fulfillment']['messages']:
                try:
                    msg_Type = getMsgType(item)
                    if "##fb_name" in item[msg_Type].lower() or "anh/chị" in item[msg_Type].lower() or "anh/chi" in \
                            item[msg_Type].lower():
                        item[msg_Type] = item[msg_Type].replace('##fb_name', facebookName)
                        for genderItemL in arrGengerL:
                            item[msg_Type] = item[msg_Type].replace(genderItemL, genderL)
                        for genderItemU in arrGengerU:
                            item[msg_Type] = item[msg_Type].replace(genderItemU, genderU)

                except:
                    pass
            self.result = self.req['result']['fulfillment']
