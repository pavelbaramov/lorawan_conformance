"""
This module defines the format of the different message interaction with the user
interface.
"""
#################################################################################
# MIT License
#
# Copyright (c) 2018, Pablo D. Modernell, Universitat Oberta de Catalunya (UOC).
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#################################################################################
import json
from uuid import uuid4
import pika
import abc
import time

from user_interface import API_VERSION
from message_queueing import DEFAULT_EXCHANGE


LEVEL_ERR = "error"
LEVEL_HL = "highlighted"
LEVEL_INFO = "info"


class MessageProperties(object):
    def __init__(self,
                 content_type="application/json",
                 message_id="",
                 timestamp=int(time.time()),
                 reply_to="",
                 correlation_id=str(uuid4())):
        self._properties = {
            "content_type": content_type,
            "message_id": message_id,
            "timestamp": timestamp,
            "reply_to": reply_to,
            "correlation_id": correlation_id
        }

    def __str__(self):
        return json.dumps(self._properties, indent=4, sort_keys=True)

    @property
    def content_type(self):
        return self._properties["content_type"]

    @content_type.setter
    def content_type(self, message_type):
        self._properties["content_type"] = message_type

    @property
    def message_id(self):
        return self._properties["message_id"]

    @message_id.setter
    def message_id(self, message_id):
        self._properties["message_id"] = message_id

    @property
    def timestamp(self):
        return self._properties["timestamp"]

    @timestamp.setter
    def timestamp(self, timestamp):
        self._properties["timestamp"] = timestamp

    @property
    def reply_to(self):
        return self._properties["reply_to"]

    @reply_to.setter
    def reply_to(self, reply_to):
        self._properties["reply_to"] = reply_to

    @property
    def correlation_id(self):
        return self._properties["correlation_id"]

    @correlation_id.setter
    def correlation_id(self, correlation_id):
        self._properties["correlation_id"] = correlation_id


class SessionConfigurationBody(object):
    def __init__(self,
                 json_session_configuration=None,
                 api_version=API_VERSION,
                 message_id="",
                 testcases=None,
                 session_id="",
                 testing_tools="f-interop/flora",
                 users=None):
        if json_session_configuration:
            self._body = json.loads(json_session_configuration)
        else:
            self._body = {
                "_api_version": api_version,
                "testcases": testcases
            }
            if not testcases:
                self._body["testcases"] = []

    def __str__(self):
        return json.dumps(self._body)

    @property
    def _api_version(self):
        if "_api_version" in self._body:
            return self._body["_api_version"]

    @_api_version.setter
    def _api_version(self, _api_version):
        self._body["_api_version"] = _api_version

    @property
    def testcases(self):
        if "testcases" in self._body:
            return self._body["testcases"]

    @testcases.setter
    def testcases(self, testcases):
        self._body["testcases"] = testcases


class InputField(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, name="default name", label="default label", value="default value"):
        self._field = {
                    "name": name,
                    "type": None,
                    "label": label,
                    "value": value
                }

    def __str__(self):
        return json.dumps(self._field, indent=4, sort_keys=True)

    @property
    def type(self):
        return self._field["type"]

    @property
    def field_dict(self):
        return self._field

    @property
    def name(self):
        return self._field["name"]

    @name.setter
    def name(self, name):
        self._field["name"] = name

    @property
    def label(self):
        return self._field["label"]

    @label.setter
    def label(self, label):
        self._field["label"] = label

    @property
    def value(self):
        return self._field["value"]

    @value.setter
    def value(self, value):
        self._field["value"] = value


class ParagraphField(InputField):
    def __init__(self, name="default name", label="default label", value="sthg2show"):
        super().__init__(name=name, label=label, value=value)
        self._field["type"] = "p"

    def add_line(self, new_line):
        self._field["value"] += "\n"+new_line


class TextInputField(InputField):
    def __init__(self, name="default name", label="default label", value="default value"):
        super().__init__(name=name, label=label, value=value)
        self._field["type"] = "text"


class ButtonInputField(InputField):
    def __init__(self, name="default name", label="default label", value="default value"):
        super().__init__(name=name, label=label, value=value)
        self._field["type"] = "button"


class InputFormBody(object, metaclass=abc.ABCMeta):
    def __init__(self, title="Input Title", level=LEVEL_INFO, tag_key=None, tag_value=None):
        self._body = {
            "title": title,
            "level": level,
            "fields": []
        }
        if tag_key and tag_value:
            self._body["tags"] = {tag_key: tag_value}

    def __str__(self):
        return json.dumps(self._body, indent=4, sort_keys=True)

    @property
    def title(self):
        return self._body["title"]

    @title.setter
    def title(self, title):
        self._body["title"] = title

    @property
    def level(self):
        return self._body["level"]

    @level.setter
    def level(self, level):
        self._body["level"] = level

    def add_field(self, new_field):
        self._body["fields"].append(new_field.field_dict)

    def get_parsed_reply(self, reply_body):
        """ Returns a dict with the response values {name:value}."""
        reply = json.loads(reply_body.decode())
        parsed_reply = dict()
        for field in self._body["fields"]:
            for reply_field in reply["fields"]:
                if field["name"] in reply_field:
                    parsed_reply[field["name"]] = reply_field[field["name"]]
                    break

        return parsed_reply


class RPCRequest(object):
    def __init__(self, request_key, channel, body):
        self.channel = channel
        self.connection = channel.connection
        self.request_key = request_key
        self.body = body
        self.reply_to = request_key.replace("request", "reply")
        self.correlation_id = None
        self.response_body = None
        self.consumer_tag = None
        self.temporary_queue = None

    def on_response(self, ch, method, properties, body):
        if self.correlation_id == properties.correlation_id:
            self.response_body = body
            ch.basic_ack(delivery_tag=method.delivery_tag)
            ch.stop_consuming(consumer_tag=self.consumer_tag)

    def wait_response(self, timeout_seconds=None):
        # TODO: handle timeout
        queue_result = self.channel.queue_declare(exclusive=True)
        self.temporary_queue = queue_result.method.queue
        self.channel.queue_bind(queue=self.temporary_queue,
                                exchange=DEFAULT_EXCHANGE,
                                routing_key=self.reply_to)
        self.consumer_tag = self.channel.basic_consume(consumer_callback=self.on_response,
                                                       no_ack=False,
                                                       queue=self.temporary_queue)
        self.correlation_id = str(uuid4())
        time.sleep(1)
        self.channel.basic_publish(exchange=DEFAULT_EXCHANGE,
                                   routing_key=self.request_key,
                                   properties=pika.BasicProperties(reply_to=self.reply_to,
                                                                   correlation_id=self.correlation_id),
                                   body=self.body)

        while self.response_body is None:
            self.connection.process_data_events()
        return self.response_body

