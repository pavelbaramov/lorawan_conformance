import pika
import message_queueing


class ConfigurationReply(object):
    def __init__(self, reply_to=None, correlation_id=None, body=""):
        self.reply_to = reply_to
        self.correlation_id = correlation_id
        self.body = body
        self._mq_interface = message_queueing.MqInterface()

    @property
    def ready_to_send(self):
        return self.reply_to is not None and self.correlation_id is not None

    def send(self):
        if self.ready_to_send:
            self._mq_interface.channel.basic_publish(exchange='amq.topic',
                                                     routing_key=self.reply_to,
                                                     properties=pika.BasicProperties(
                                                         correlation_id=self.correlation_id),
                                                     body=self.body)
