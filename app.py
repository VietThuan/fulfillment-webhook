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
import facebook

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    # graph = facebook.GraphAPI(access_token="EAACEdEose0cBAPPdSBLUTyYtTwXX8JxXh5D8mZCVlOanXMvehV7GUD04rwXaUmVKTc1vCypjUBFfXlOCp748GQNGTEoSh4YTDLzZBh4llLiOLi4P0niYs2JEeG0obgJCzJeORCxZBMvUFDAV2Lqqfmu6Tcqhfp2l8vCNIlXF1lPJHrdCO5qfDMWxMelujSBR9aB6ZBmRKAZDZD", version="2.1")
    # graph.put_object(parent_object='me', connection_name='feed',message='Hello, world')


    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    action = req.get("result").get("action")
    parameters = req.get("result").get("parameters")
    res = {}
    if action == "yahooWeatherForecast":
        baseurl = "https://query.yahooapis.com/v1/public/yql?"
        yql_query = makeYqlQuery(req)
        if yql_query is None:
            return {}
        yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
        result = urlopen(yql_url).read()
        data = json.loads(result)
        res = makeWebhookResult(data)
        return res
    elif action == "input.LoiAMIS":
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

    if len(res) > 0:
        return makeWebhookResult1(res)
    else:
        return {}

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
        "source": "apiai-weather-webhook-sample"
    }

def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today the weather in " + location.get('city') + ": " + condition.get('text') + \
             ", And the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
