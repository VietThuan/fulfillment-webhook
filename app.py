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
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
from fbchat import Client
from fbchat.models import *
import http.client

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

FANPAGE_TOKEN = 'EAAQhILYOQ08BABYVdqnAaqWQ4wrifzM6y86SKV9mWn4u6DtIOuBxZBBFwfceJSSpl5jZC0dFZA4hq7fcgZCKMyYkNzsvPrssLFEbZAPciXGMliOf7tYuzLpq8Y5o7ZA4T0zbnZCVktxOZBJ7ZBYciD86TcpcRfhUgZAZCGjI47i3PSs5A4PgAdYZCmpu'

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

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
    # Phải được chat lên từ facebook thì mới xử l
    if not isContainKey("originalRequest;source",req, "facebook"):
        return {}

    action = req["result"]["action"]
    parameters = req["result"]["parameters"]
    senderID = req["result"]["contexts"][0]["parameters"]["facebook_sender_id"]


    res = {}
    if action == "input.LoiAMIS":
        strErrorCode = parameters.get("LoiAMIS")
        if strErrorCode == "HRMLoginFail":
            res= "Không đăng nhập được vào hệ thống HRM. Anh/Chị làm theo hướng dẫn sau: http://kb.misa.com.vn/#knowledgeid=90"
        elif strErrorCode == "LoginFail":
            res= "Không đăng nhập được vào hệ thống AMIS. Anh/Chị làm theo hướng dẫn sau: http://kb.misa.com.vn/#knowledgeid=548"
        else:
            sendMsgtoUser('Có một khác hàng không hỗ trợ được')
            res = "Em rất xin lỗi Anh (Chị) vấn đề này em chưa hỗ trợ được ạ. Anh (Chị) vui lòng gửi email tới support@misa.com.vn hoặc hỏi đáp trên http://forum.misa.com.vn/ giúp em nhé. Cám ơn anh chị ạ !"

    elif action == "input.unknown":
        sendMsgtoUser('Có một khác hàng không hỗ trợ được')
        res = "Em rất xin lỗi Anh (Chị) vấn đề này em chưa hỗ trợ được ạ. Anh (Chị) vui lòng gửi email tới support@misa.com.vn hoặc hỏi đáp trên http://forum.misa.com.vn/ giúp em nhé. Cám ơn anh chị ạ !"

    if not len(res) > 0 and senderID != "":
        res = req.get("result").get("fulfillment").get("speech")
        if "##facebook_name" in res.lower()  or "##gender" in res.lower():
           res = res.replace('##facebook_name', get_info(senderID).get("last_name"))
           res = res.replace('##gender', makeVietNameGender(get_info(senderID).get("gender"), False))
           res = res.replace('##Gender', makeVietNameGender(get_info(senderID).get("gender"), True))
    return makeWebhookResult1(res)

def sendMsgtoUser(msg):
    thread_id = '100007842240328'
    thread_type = ThreadType.USER
    client = Client("0966880147", "mekiep")
    client.send(Message(text=msg), thread_id=thread_id, thread_type=thread_type)

def makeWebhookResult1(data):
    return {
        "speech": data,
        "displayText": data,
        # "data": data,
        # "contextOut": [],
        "source": "dialogflow-webhook"
    }

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
