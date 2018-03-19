import logging

import cow.patterns
from cow import ConfigBase


@cow.patterns.singleton
class ChatbotConfig(ConfigBase):
    FanpageToken = 'EAACPPDsQaS0BAExsREUHTkstZBZArAzIl2j1maWqp1rA7UZCrV1H02tzaprt9VfU4zy6KUdB7J1Bf7gyF0hkEphFAdYKq3PWEtiZBmEOO7ZAGjpH1LifSYiYiczJnpQoggSMyMQSQb0ZAlAc7bdB0MaijYoqpDW74C9nYzrAP7UwZDZD'
    GenderUpper = 'Anh/Chị;Anh/Chi;Anh/chi;Anh/chị;anh/Chi;anh/Chị'
    GenderLower = 'anh/chị;anh/chi'
    ThreadTimeout = 4
    CacheMaxsize = 1000
    CacheTTL = 1800
    LogStashServerEndpoint = '117.6.16.176'
    LogStashServerPort = 91
    MaxThread = 20
    DFClientToken = 'dff9b6906ff94bed830a10697ec4e658'
    FallbackLimit = 4


cfg = ChatbotConfig()
cfg.merge_env()

logging.warning('Start config:' + str(cfg))
