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

FANPAGE_TOKEN = 'EAARJGq0hgDoBAMu87Yn7f9uR6ZBAgAZCc0qYuuOqXBipUsdpWggqwQ3riK5xq1glhQPSniKG5FXciM74nyW5xxJItIElUZBLEGWUCGz2Gm11Y1ALzA0AjYQXomg6oHi9rJOtjtcQFIgoQMxhcHzLg8ZBnThrJhKUiIimXZB5d7dJAYQn5To3D'

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
    for item in req["result"]["contexts"]:
        try:
            senderID = item["parameters"]["facebook_sender_id"]
            break
        except:
            pass
    res = {}
    if not len(res) > 0 and senderID != "":
        res = req.get("result").get("fulfillment").get("speech")
        if "##facebook_name" in res.lower() or "anh/chị" in res.lower():
           res = res.replace('##facebook_name', get_info(senderID).get("first_name") + get_info(senderID).get("last_name") )
           res = res.replace('anh/chị', makeVietNameGender(get_info(senderID).get("gender"), False))
           res = res.replace('Anh/Chị', makeVietNameGender(get_info(senderID).get("gender"), True))
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
