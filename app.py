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

from future.standard_library import install_aliases
from lru import lru_cache_function

install_aliases()

import json
import os
from fbchat import Client
from fbchat.models import *
import http.client

from flask import Flask
from flask import request
from flask import jsonify
from enum import Enum

# Flask app should start in global layout
app = Flask(__name__)

FANPAGE_TOKEN = 'EAARJGq0hgDoBAEIfurZCZCEeZApeO0rcV1XpKiqZAMnvgkw3zxgX3MHSJYx5fAZCogwzzmIzdfZAXKjLgEAK1lKyIKs1iPcs21ukFcEQV2mX5XHXzw27h62sAAjoZClEqgpVMvv72DZATZCoiZCuklq1otPYCrdlREQAzX5d2gOntw5g24lV3P49S7'


# Loai message cua fb
class MessagesType(Enum):
    TEXTRESPORSE = 0
    QUICKREPLY = 2
    CARD = 1

@app.route('/webhook', methods=['POST'])
def webhook():
    return jsonify(processRequest(request.get_json(silent=True, force=True)))

def isContainKey(data,dic,value):
    datas = data.split(";")
    for item in datas:
        if item not in dic:
            return False
        else:
            dic = dic.get(item)
    if value != "" and value != dic :
        return False
    return True

def processRequest(req):
    # Phải được chat lên từ facebook thì mới xử ly
    if not isContainKey("originalRequest;source",req, "facebook"):
        return {}
    for item in req["result"]["contexts"]:
        try:
            senderID = item["parameters"]["facebook_sender_id"]
            if req['result']['resolvedQuery'].lower() == "facebook_welcome":
                get_info(senderID)
            break
        except:
            pass
    if senderID != "":
        for item in req['result']['fulfillment']['messages']:
            try:
                contentType = ""
                if item['type'] == MessagesType.TEXTRESPORSE.value:
                    contentType = 'speech'
                if item['type'] == MessagesType.QUICKREPLY.value:
                    contentType = 'title'
                if item['type'] == MessagesType.CARD.value:
                    contentType = 'subtitle'

                if "##fb_name" in item[contentType].lower() or "anh/chị" in item[contentType].lower():
                    item[contentType] = item[contentType].replace('##fb_name',
                                                            get_info(senderID).get("first_name") + get_info(
                                                                senderID).get("last_name"))
                    item[contentType] = item[contentType].replace('anh/chị',
                                                            makeVietNameGender(get_info(senderID).get("gender"), False))
                    item[contentType] = item[contentType].replace('Anh/Chị',
                                                            makeVietNameGender(get_info(senderID).get("gender"), True))
            except:
                pass
    return req['result']['fulfillment']

def sendMsgtoUser(msg):
    thread_id = '100007842240328'
    thread_type = ThreadType.USER
    client = Client("0966880147", "mekiep")
    client.send(Message(text=msg), thread_id=thread_id, thread_type=thread_type)

# Luu cache trong 30 phut
@lru_cache_function(max_size=1024, expiration=30*60)
def get_info(id):
    fields='first_name,last_name,profile_pic,locale,timezone,gender'
    conn = http.client.HTTPSConnection("graph.facebook.com")
    conn.request("GET", "/v2.11/{}?fields={}&access_token={}".format(id,fields,FANPAGE_TOKEN))

    res = conn.getresponse()
    data = res.read()

    obj=json.loads( data.decode("utf-8"))
    return obj

def makeVietNameGender(value,isUpper):
    if value == "male":
        if isUpper ==True:
            return "Anh"
        else:
            return "anh"
    elif value == "female":
        if isUpper ==True:
            return "Chị"
        else:
            return "chị"
    return "Anh/Chị"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')

