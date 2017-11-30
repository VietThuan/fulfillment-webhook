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

from config import ChatbotConfig
from facebook_util import isContainKey
from waiting_process import SendMessageTask, GetGenderTask

install_aliases()

import os
from flask import Flask
from flask import request


# Flask app should start in global layout
app = Flask(__name__)

cfg = ChatbotConfig()


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    # Chỉ xử lý câu trả lời cho hội thoại trên facebook
    if not isContainKey("originalRequest;source", req, "facebook"):
        return {}

    for item in req["result"]["contexts"]:
        try:
            senderID = item["parameters"]["facebook_sender_id"]
            break
        except:
            pass

    return SendMessageTask(GetGenderTask(req, senderID), senderID).run()


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
