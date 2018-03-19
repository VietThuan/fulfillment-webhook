import logging
import threading
import traceback

import requests
from flask import jsonify

import util
from config import ChatbotConfig
from enums import getMsgType
from facebook_messager_builder import MessageFactory
from facebook_util import get_facebook_sender_id, make_viet_name_gender

cfg = ChatbotConfig()

number_of_thread = 0


# Lớp gửi câu trả lời cho Facebook
class SendMessageTask:
    def __init__(self, generate_message_task, senderId):
        self.subject = generate_message_task
        self.senderId = senderId

    def run(self):
        # Tạo thread xử lý câu trả lời cho Facebook (cập nhật danh xưng và tên cho câu trả lời)
        create_response_thread = threading.Thread(target=self.execute, args=())
        create_response_thread.start()

        create_response_thread.join(timeout=int(cfg.ThreadTimeout))
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
            if not util.is_contain_key("platform", item, 'facebook'):
                continue
            data_json = MessageFactory().create_message(item['type'], self.senderId, item)
            res = requests.post(
                "https://graph.facebook.com/v2.11/me/messages",
                params={"access_token": cfg.FanpageToken},
                headers={"Content-Type": "application/json"},
                data=data_json
            )
            logging.debug("Send result: {}".format(str(res)))

    def execute(self):
        global number_of_thread
        number_of_thread = number_of_thread + 1
        if number_of_thread > int(cfg.MaxThread):
            logging.warning("number of thread to large:" + str(number_of_thread))
        self.subject.run()
        number_of_thread = number_of_thread - 1


# Tạo câu trả lời cho Facebook
class GetGenderTask:
    def __init__(self, req, senderId):
        self.senderId = senderId
        self.req = req
        self.result = ''

    def run(self):
        if self.senderId != "":
            sender_info = get_facebook_sender_id(self.senderId)

            gender_l = make_viet_name_gender(sender_info.get("gender"), False)
            gender_u = make_viet_name_gender(sender_info.get("gender"), True)
            facebook_name = sender_info.get("first_name", '') + " " + sender_info.get("last_name", '')

            arr_gender_u = cfg.GenderUpper.split(";")
            arr_gender_l = cfg.GenderLower.split(";")

            for item in self.req['result']['fulfillment']['messages']:
                try:
                    msg_type = getMsgType(item)
                    if "##fb_name" in item[msg_type].lower() or "anh/chị" in item[msg_type].lower() or "anh/chi" in \
                            item[msg_type].lower():
                        item[msg_type] = item[msg_type].replace('##fb_name', facebook_name)
                        for genderItemL in arr_gender_l:
                            item[msg_type] = item[msg_type].replace(genderItemL, gender_l)
                        for genderItemU in arr_gender_u:
                            item[msg_type] = item[msg_type].replace(genderItemU, gender_u)
                except:
                    logging.error("Error on GetGenderTask.run(), traceback:" + traceback.format_exc())
            self.result = self.req['result']['fulfillment']
