# -*- coding:utf8 -*-
# !/usr/bin/env python
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import pycommon
from future.standard_library import install_aliases
from lru import lru_cache_function

from config import ChatbotConfig

install_aliases()

import json
import os
from fbchat import Client
from fbchat.models import *
import http.client
import time
import threading
import queue
import requests

from flask import Flask
from flask import request
from flask import jsonify
from enum import Enum

# Flask app should start in global layout
app = Flask(__name__)

cfg = ChatbotConfig()
cfg.merge_file(pycommon.get_callee_path() + "/config.ini")
cfg.merge_env()

print(cfg)


# Loai message cua fb
class MessagesType(Enum):
    TEXTRESPORSE = 0
    QUICKREPLY = 2
    CARD = 1


# Loai message cua fb
class MessagesTitle():
    TEXTRESPORSE = 'speech'
    QUICKREPLY = 'title'
    CARD = 'subtitle'


@app.route('/webhook', methods=['POST'])
def webhook():
    my_queue = queue.Queue()
    req = request.get_json(silent=True, force=True)

    # Phải được chat lên từ facebook thì mới xử lý
    if not isContainKey("originalRequest;source", req, "facebook"):
        return {}

    for item in req["result"]["contexts"]:
        try:
            senderID = item["parameters"]["facebook_sender_id"]
            break
        except:
            pass

    thread1 = threading.Thread(target=processRequest, args=(req, senderID, my_queue))
    thread1.start()
    thread1.join(timeout=4)
    if thread1.is_alive():
        res = {
            "speech": "Chờ em một chút nhé!",
            "displayText": "Chờ em một chút nhé!",
            "source": "MISA-webhook"
        }
        thread2 = threading.Thread(target=send_message, args=(senderID, my_queue, thread1))
        thread2.start()
        return jsonify(res)
    else:
        return jsonify(my_queue.get())
        # send_message(req["result"]["contexts"][0]["parameters"]["facebook_sender_id"],res)
        # # send_info(req['originalRequest']['data']['message']['mid'])
        # requests.post('https://api.dialogflow.com/v1/query', headers=headers, params=params, json = res['result'] ).content



        # return jsonify(res)


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


def processRequest(req, senderID, my_queue):
    if senderID != "":
        if req['result']['resolvedQuery'].lower() == "facebook_welcome" or req['result'][
            'resolvedQuery'].lower() == "welcome":
            get_info(senderID)
        genderL = makeVietNameGender(get_info(senderID).get("gender"), False)
        genderU = makeVietNameGender(get_info(senderID).get("gender"), True)
        facebookName = get_info(senderID).get("first_name") + get_info(senderID).get("last_name")
        arrGengerU = cfg.GENDER_U.split(";")
        arrGengerL = cfg.GENDER_L.split(";")

        for item in req['result']['fulfillment']['messages']:
            try:
                msg_Type = getMsgType(item)

                if "##fb_name" in item[msg_Type].lower() or "anh/chị" in item[msg_Type].lower() or "anh/chi" in item[
                    msg_Type].lower():
                    item[msg_Type] = item[msg_Type].replace('##fb_name', facebookName)
                    for genderItemL in arrGengerL:
                        item[msg_Type] = item[msg_Type].replace(genderItemL, genderL)
                    for genderItemU in arrGengerU:
                        item[msg_Type] = item[msg_Type].replace(genderItemU, genderU)

            except:
                pass
        time.sleep(5)
        my_queue.put(req['result']['fulfillment'])


def sendMsgtoUser(msg):
    thread_id = '100007842240328'
    thread_type = ThreadType.USER
    client = Client("0966880147", "mekiep")
    client.send(Message(text=msg), thread_id=thread_id, thread_type=thread_type)


def sendMsgtoPage(msg, thread_id):
    thread_type = ThreadType.PAGE
    client = Client("0966880147", "mekiep")
    client.send(Message(text=msg), thread_id=thread_id, thread_type=thread_type)


def send_message(sender_id, my_query, thread1):
    thread1.join()
    messages = my_query.get()
    '''
    Sending response back to the user using facebook graph API
    '''
    for item in messages['messages']:
        dataJSON = genDataJSON(sender_id, item)
        r = requests.post("https://graph.facebook.com/v2.6/me/messages",

                          params={"access_token": cfg.FANPAGE_TOKEN},

                          headers={"Content-Type": "application/json"},
                          data=dataJSON
                          )


def genDataJSON(sender_id, item):
    dataResult = ""
    if item['type'] == MessagesType.TEXTRESPORSE.value:
        dataResult = json.dumps({
            "recipient": {"id": sender_id},
            "message": {"text": item[getMsgType(item)]}
        })
    if item['type'] == MessagesType.QUICKREPLY.value:
        data_obj = {
            "recipient": {"id": sender_id},
            "message": {
                "text": item[getMsgType(item)],
                "quick_replies": []
            }
        }
        for v in item['replies']:
            data_obj['message']['quick_replies'].append({"content_type": "text", "title": v, "payload": v})

        dataResult = json.dumps(data_obj)

    if item['type'] == MessagesType.CARD.value:
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
        dataResult = json.dumps(data_obj)

    return dataResult


def getMsgType(item):
    msg_Type = ''
    if item['type'] == MessagesType.TEXTRESPORSE.value:
        msg_Type = MessagesTitle.TEXTRESPORSE
    if item['type'] == MessagesType.QUICKREPLY.value:
        msg_Type = MessagesTitle.QUICKREPLY
    if item['type'] == MessagesType.CARD.value:
        msg_Type = MessagesTitle.CARD
    return msg_Type


# Luu cache trong 30 phut
@lru_cache_function(max_size=1024, expiration=30 * 60)
def get_info(id):
    fields = 'first_name,last_name,profile_pic,locale,timezone,gender'
    conn = http.client.HTTPSConnection("graph.facebook.com")
    conn.request("GET", "/v2.11/{}?fields={}&access_token={}".format(id, fields, cfg.FANPAGE_TOKEN))

    res = conn.getresponse()
    data = res.read()

    obj = json.loads(data.decode("utf-8"))
    return obj


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


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
