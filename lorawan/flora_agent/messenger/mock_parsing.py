import base64
import json


class MockMessage(object):
    """
    Message containing the information sent by the command line interface to the agent mock in order
    to request data being sent to the server. It is also used to to configure de end device mock (e.g. add frequency,
    set used data rate, change session keys)
    {
        'use_dr': 2,
        'freq': 868.5,
        'frmpayload': 'QJ8pKAGAAAACBq6JhF/uO9ZeeoSq4xZMFchm3lw=',
        'port': 1,
    }
    """

    def __init__(self, json_mockmsg_str):
        """
        (str) -> (MockMessage)
        :param json_mockmsg_str: string-json formatted.
        """
        self.mock_message_dict = json.loads(json_mockmsg_str)

    def __str__(self):
        return json.dumps(self.mock_message_dict)

    def get_frmpayload_bytes(self):
        return base64.b64decode(self.mock_message_dict["frmpayload"])

    def get_fport(self):
        return self.mock_message_dict["port"]

    def get_use_dr(self):
        return self.mock_message_dict["use_dr"]

    def get_freq(self):
        return self.mock_message_dict["freq"]

    def get_fopts_bytes(self):
        return base64.b64decode(self.mock_message_dict["fopts"])

    def is_confirmed(self):
        return self.mock_message_dict["confirmed"]
