# -*- coding:utf8 -*-
# !/usr/bin/env python

from __future__ import print_function

import logging
import os
import socket
import threading
import traceback

import cow
from cachetools import TTLCache
from flask import Flask, jsonify
from flask import request
from future.standard_library import install_aliases

print(os.environ)

import util
from config import ChatbotConfig
from facebook_util import is_conversation_in_inbox
from waiting_process import SendMessageTask, GetGenderTask

install_aliases()

app = Flask(__name__)
cfg = ChatbotConfig()
name = socket.gethostname()

logger = cow.LogBuilder()
logger.add_stream_handler(level=logging.DEBUG)
logger.add_rotating_file_handler(level=logging.DEBUG, log_path="/var/log/htkh-bot-" + name)
logger.add_logstash_handler(cfg.LogStashServerEndpoint, cfg.LogStashServerPort, 'htkh-bot-' + name, logging.WARNING)
logger.build()

logging.warning("Start app with config:" + str(cfg))

current_contexts = TTLCache(maxsize=int(cfg.CacheMaxsize), ttl=int(1800))
lock = threading.RLock()

fallback_intent_count = {}


def handover(req, force=False):
    logging.warning("Execute handover, session_id[{}] sender_id[{}]".format(req['sessionId'],
                                                                            req['originalRequest']['data']['sender'][
                                                                                'id']))
    session_id = req['sessionId']
    if session_id not in fallback_intent_count:
        fallback_intent_count[session_id] = 0
    fallback_intent_count[session_id] = fallback_intent_count[session_id] + 1

    if force or fallback_intent_count[session_id] > int(cfg.FallbackLimit):
        fallback_intent_count[session_id] = 0
        handover_curl = """
        curl -X POST -H "Content-Type: application/json" -d '{{
        "recipient":{{"id":"{}"}},
        "target_app_id":263902037430900,
        "metadata":"String to pass to secondary receiver app" 
        }}' "https://graph.facebook.com/v2.12/me/pass_thread_control?access_token={}"
        """.format(util.get_sender_id(req), cfg.FanpageToken)

        logging.debug('Execute handover curl[{}] result[{}]'.
                      format(util.hide_token(handover_curl), cow.execute_curl(handover_curl, json_out=False)))

        fallback_intent_count.pop(session_id)

    return req


def reset_context(req):
    def invoke_reset_context(req):
        if req['sessionId'] not in current_contexts:
            return
        context_names = current_contexts[req['sessionId']].split(";")

        logging.debug("Reset context, Contexts Delete: {}".format(current_contexts[req['sessionId']]))

        for v in context_names:
            if len(v.strip()) == 0:
                continue
            s = 'curl -X DELETE \
            "https://api.dialogflow.com/v1/contexts/{}?timezone=Asia/Saigon&lang=en&sessionId={}"\
            -H "Authorization: Bearer {}" -H "Content-Type: application/json"'

            replaced = s.format(v, req['sessionId'], cfg.DFClientToken)

            logging.debug(
                'Reset context curl[{}] result[{}]'.format(util.hide_token(replaced), cow.execute_curl(replaced, json_out=False)))

    t = threading.Thread(target=invoke_reset_context, args=(req,))
    t.daemon = True
    t.start()

    session_id = req['sessionId']
    if session_id in fallback_intent_count:
        fallback_intent_count.pop(session_id)

    return req


# Mapping action trong DF với hàm của webhook
action_resolve = {
    'xoangucanh': reset_context,
    'input.unknown': handover
}


def set_to_current_old(session_id, list_context):
    global current_contexts
    values = ';'.join(list_context)
    if session_id in current_contexts:
        logging.debug('Old contexts:' + values)
    current_contexts[session_id] = values


def set_to_current(session_id, list_context):
    global current_contexts
    values = ';'.join(list_context)
    if session_id in current_contexts:
        logging.debug('New contexts:' + values)
    current_contexts[session_id] = values


@app.route('/webhook', methods=['POST'])
def webhook():
    global current_contexts

    req = request.get_json(silent=True, force=True)
    actions = req['result']['action'].split(';')

    facebook_sender_id = util.get_facebook_sender_id(req)

    if facebook_sender_id is None:
        logging.error("facebook_sender_id not found in parameters, req: " + str(req))
        return jsonify({})

    try:

        has_action_xoa_ngu_canh = any(x == 'xoangucanh' for x in actions)
        logging.debug('có action xóa ngữ cảnh: {}'.format(has_action_xoa_ngu_canh))

        if not has_action_xoa_ngu_canh:
            key = req['sessionId']
            set_to_current_old(key, [x['name'] for x in req['result']['contexts']])

        for action in actions:
            if action in action_resolve:
                req = action_resolve[action](req)

        if has_action_xoa_ngu_canh:
            key = req['sessionId']
            if key in current_contexts:
                set_to_current(key, set([x['name'] for x in req['result']['contexts']]) - set(
                    current_contexts[key].split(";")))
            else:
                set_to_current(key, set([x['name'] for x in req['result']['contexts']]))

        logging.debug('Current context:' + current_contexts[req['sessionId']])
    except:
        logging.error("Error when execute action:" + str(traceback.format_exc()))

    if is_conversation_in_inbox(facebook_sender_id):
        # nếu conversation đang trong inbox thì không trả lời và coi như không hiểu
        handover(req, force=True)

    return SendMessageTask(GetGenderTask(req, facebook_sender_id), facebook_sender_id).run()


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logging.debug("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0', threaded=True)
