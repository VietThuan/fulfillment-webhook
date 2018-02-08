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
    print(pycommon.execute_curl(replaced))


fallback_intent_count = {}


def khong_hieu(req):
    logging.warning("Ko hieu")
    session_id = req['sessionId']
    if session_id not in fallback_intent_count:
        fallback_intent_count[session_id] = 0
    fallback_intent_count[session_id] = fallback_intent_count[session_id] + 1

    if fallback_intent_count[session_id] > cfg.FALLBACK_LIMIT:
        handover_curl = """
        curl -X POST -H "Content-Type: application/json" -d '{{
  "recipient":{{"id":"{}"}},
  "target_app_id":263902037430900,
  "metadata":"String to pass to secondary receiver app" 
}}' "https://graph.facebook.com/v2.6/me/pass_thread_control?access_token={}"
""".format(req['originalRequest']['data']['sender']['id'], cfg.FANPAGE_TOKEN)
        print(handover_curl)
        result = pycommon.execute_curl(handover_curl)
        logging.warning("Fallback exceed maximum times, forward control to human:" + str(result))
        fallback_intent_count.pop(session_id)

    return req


def reset_content(req):
    t = threading.Thread(target=invoke_reset_context, args=(req['sessionId'],))
    t.daemon = True
    t.start()
    return req


# Mapping action trong DF với hàm của webhook
action_resolve = {
    'xoangucanh': reset_content,
    'input.unknown': khong_hieu
}


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    # print(req)
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
