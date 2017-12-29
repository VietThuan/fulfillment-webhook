# -*- coding:utf8 -*-
# !/usr/bin/env python

from __future__ import print_function

import logging
import threading
import traceback

import pycommon
from future.standard_library import install_aliases

from config import ChatbotConfig
from facebook_util import isContainKey
from waiting_process import SendMessageTask, GetGenderTask

install_aliases()

import os
from flask import Flask, jsonify
from flask import request

app = Flask(__name__)

cfg = ChatbotConfig()

logger = pycommon.LogBuilder()
logger.init_rotating_file_handler(cfg.LogPath + "/logs")
logger.init_logstash_handler(cfg.LogStashServerEndpoint, cfg.LogStashServerPort, 'htkh-bot-sme', logging.WARNING)
logger.init_stream_handler()
logger.build()

logging.error("Start app with config:" + str(cfg))

def invoke_reset_context(session_id):
    import time
    time.sleep(1)
    s = 'curl -H "Authorization: Bearer {}" \
                               "https://api.dialogflow.com/v1/query?v=20150910&query=test&resetContexts=true&timezone=Asia/Saigon&lang=en&sessionId={}"'
    replaced = s.format(cfg.DF_TOKEN, session_id)
    print( pycommon.execute_curl(replaced))


def reset_content(req):
    t = threading.Thread(target=invoke_reset_context, args=(req['sessionId'],))
    t.daemon = True
    t.start()

# Mapping action trong DF với hàm của webhook
action_resolve = {
    'xoangucanh': reset_content
}

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    actions = req['result']['action'].split(';')

    try:
        for action in actions:
            if action in action_resolve:
                req = action_resolve[action](req)
    except:
        logging.error("Error when execute action:" + str(traceback.format_exc()))

    # Chỉ xử lý câu trả lời cho hội thoại trên facebook
    if not isContainKey("originalRequest;source", req, "facebook"):
        return jsonify({})

    senderID = None
    for item in req["result"]["contexts"]:
        try:
            senderID = item["parameters"]["facebook_sender_id"]
            break
        except:
            pass
    if senderID is None:
        logging.error("facebook_sender_id not found in parameters, req: " + str(req))
        return jsonify({})

    return SendMessageTask(GetGenderTask(req, senderID), senderID).run()


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0', threaded=True)
