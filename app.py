# -*- coding:utf8 -*-
# !/usr/bin/env python

from __future__ import print_function

import logging
import threading
import traceback

import pycommon
from cachetools import TTLCache
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

current_contexts = TTLCache(maxsize=int(cfg.CACHE_MAXSIZE), ttl=int(1800))
lock = threading.RLock()


def invoke_reset_context(req):
    if req['sessionId'] not in current_contexts:
        return
    import time
    contextNames = current_contexts[req['sessionId']].split(";")

    if set([x['name'] for x in req['result']['contexts']]) == set(contextNames):
        print("Bang nhau: {}".format(current_contexts[req['sessionId']]))
        return

    print("Contexts Delete: {}".format(current_contexts[req['sessionId']]))
    # current_contexts.pop(session_id)

    # time.sleep(1)

    for v in contextNames:
        if len(v.strip())==0:
            continue
        s = 'curl -X DELETE \
        "https://api.dialogflow.com/v1/contexts/{}?timezone=Asia/Saigon&lang=en&sessionId={}"\
        -H "Authorization: Bearer {}" -H "Content-Type: application/json"'

        replaced = s.format(v, req['sessionId'], cfg.DF_TOKEN)
        print(replaced)
        print(pycommon.execute_curl(replaced, json_out=False))


def reset_content(req):
    t = threading.Thread(target=invoke_reset_context, args=(req,))
    t.daemon = True
    t.start()
    return req


# Mapping action trong DF với hàm của webhook
action_resolve = {
    'xoangucanh': reset_content
}


def set_to_current_old(session_id, list_context):
    global current_contexts
    if session_id in current_contexts:
        print("Old :" + ";".join(list_context))
    values = ';'.join(list_context)
    current_contexts[session_id] = values


def set_to_current(session_id, list_context):
    global current_contexts
    if session_id in current_contexts:
        print("New :" + ";".join(list_context))
    values = ';'.join(list_context)
    current_contexts[session_id] = values


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    global current_contexts

    if req['sessionId'] not in current_contexts:
        print('cache ko co :'+req['sessionId'])
    else:
        print('cache co session id: ' + req['sessionId'] )

    actions = req['result']['action'].split(';')

    try:
        hasActionXoangucanh = False
        for action in actions:
            if action == 'xoangucanh':
                hasActionXoangucanh = True

        print("hasActionXoangucanh: {}".format(hasActionXoangucanh))


        if hasActionXoangucanh == False:
            key = req['sessionId']
            set_to_current_old(key, [x['name'] for x in req['result']['contexts']])

            # hasActionXoangucanh = True
        # if  hasActionXoangucanh:

        for action in actions:
            if action in action_resolve:
                req = action_resolve[action](req)

        if hasActionXoangucanh == True:
            key = req['sessionId']
            if key in current_contexts:
                set_to_current(key, set([x['name'] for x in req['result']['contexts']]) - set(
                    current_contexts[key].split(";")))
            else:
                set_to_current(key, set([x['name'] for x in req['result']['contexts']]))

        print("Current Context: {}".format(current_contexts[req['sessionId']]))

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
