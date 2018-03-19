from enum import Enum


class MessagesType(Enum):
    TEXTRESPORSE = 0
    QUICKREPLY = 2
    CARD = 1


class MessagesTitle():
    TEXTRESPORSE = 'speech'
    QUICKREPLY = 'title'
    CARD = 'subtitle'


def getMsgType(item):
    msg_type = ''
    if item['type'] == MessagesType.TEXTRESPORSE.value:
        msg_type = MessagesTitle.TEXTRESPORSE
    if item['type'] == MessagesType.QUICKREPLY.value:
        msg_type = MessagesTitle.QUICKREPLY
    if item['type'] == MessagesType.CARD.value:
        msg_type = MessagesTitle.CARD
    return msg_type
