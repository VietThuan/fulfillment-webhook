import json

import cow.patterns

from enums import MessagesType, getMsgType


@cow.patterns.singleton
class MessageFactory:
    """
    Tạo câu trả lời cho facebook thông qua graph API
    """

    def __init__(self):
        self.dic = {MessagesType.TEXTRESPORSE.value: MessageFactory._create_text,
                    MessagesType.QUICKREPLY.value: MessageFactory._create_quick,
                    MessagesType.CARD.value: MessageFactory._create_card, }

    @classmethod
    def _create_quick(cls, sender_id, item):
        data_obj = {
            "recipient": {"id": sender_id},
            "message": {
                "text": item[getMsgType(item)],
                "quick_replies": []
            }
        }
        for v in item['replies']:
            data_obj['message']['quick_replies'].append({"content_type": "text", "title": v, "payload": v})

        return json.dumps(data_obj)

    @classmethod
    def _create_card(cls, sender_id, item):
        data_obj = {
            "recipient": {"id": sender_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "generic",
                        "elements": [
                            {
                                "title": item['title'],
                                "image_url": item['imageUrl'],
                                "subtitle": item['subtitle'],
                                "buttons": []
                            }
                        ]
                    }
                }
            }
        }
        for v in item['buttons']:
            data_obj['message']['attachment']['payload']['elements'][0]['buttons'].append(
                {"type": "web_url", "url": v['postback'], "title": v['text']})
        return json.dumps(data_obj)

    @classmethod
    def _create_text(cls, sender_id, item):
        return json.dumps({
            "recipient": {"id": sender_id},
            "message": {"text": item[getMsgType(item)]}
        })

    def create_message(self, type, sender_id, item):
        if type not in self.dic:
            raise Exception("Type not support: {}".format(type))
        return self.dic[type](sender_id, item)
