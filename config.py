from pycommon import ConfigBase

import pycommon.patterns


@pycommon.patterns.singleton
class ChatbotConfig(ConfigBase):
    FANPAGE_TOKEN = None
    GENDER_U = None
    GENDER_L = None
    THREAD_TIMEOUT = None
    CACHE_MAXSIZE = None
    CACHE_TTL = None

cfg = ChatbotConfig()
cfg.merge_file(pycommon.get_callee_path() + "/config.ini")
cfg.merge_env()
