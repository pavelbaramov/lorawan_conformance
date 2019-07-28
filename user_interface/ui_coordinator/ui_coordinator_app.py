import json
import pika

# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
import flask  # from flask import Flask, render_template, url_for, copy_current_request_context
from random import random
from time import sleep
from threading import Thread, Event

import user_interface.ui_coordinator.app.forms
import message_queueing
import parameters.message_broker
import user_interface.ui_reports
import user_interface.ui_coordinator.rpc_reply

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True

# turn the flask app into a socketio app
socketio = SocketIO(app)

# random number Generator Thread
thread = Thread()
thread_stop_event = Event()

refresh_count = 0
config_received = 0

configuration_reply = user_interface.ui_coordinator.rpc_reply.ConfigurationReply()
device_credentials_reply = user_interface.ui_coordinator.rpc_reply.ConfigurationReply()
start_reply = user_interface.ui_coordinator.rpc_reply.ConfigurationReply()


class UiListener(Thread):
    def __init__(self):
        self.mq_interface = message_queueing.MqInterface()
        print("Declaring queue.")
        self.mq_interface.declare_and_consume(queue_name="display_gui",
                                              routing_key=parameters.message_broker.routing_keys.ui_all_users + '.display',
                                              callback=self.process_received_display_msg,
                                              exclusive=False)
        self.mq_interface.declare_and_consume(queue_name="configuration_request",
                                              routing_key=parameters.message_broker.routing_keys.configuration_request,
                                              callback=self.process_configuration_request_msg,
                                              exclusive=False)
        self.mq_interface.declare_and_consume(queue_name="request_action_gui",
                                              routing_key=parameters.message_broker.routing_keys.ui_all_users + '.request',
                                              callback=self.process_gui_action_request_msg,
                                              exclusive=False)
        super(UiListener, self).__init__()

    def process_received_display_msg(self, ch, method, properties, body):
        # infinite loop of magical random numbers
        print(f"Received message to display: {body}")
        message_html_str = user_interface.ui_reports.InputFormBody.build_from_json(body).to_html()
        socketio.emit('display_gui', message_html_str, namespace='/test')

    def process_configuration_request_msg(self, ch, method, properties, body):
        global config_received
        # infinite loop of magical random numbers
        print(f"Received configuration request: {body}")
        config_received += 1
        socketio.emit('user_alerts', "<p> Configuration sent to TAS!!</p>", namespace='/test')
        configuration_reply.reply_to = properties.reply_to
        configuration_reply.correlation_id = properties.correlation_id
        ch.basic_publish(exchange='amq.topic',
                         routing_key=properties.reply_to,
                         properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                         body=json.dumps({"api_version": "1.0.1", "testcases": ["td_lorawan_act_02"]}))
        # ch.basic_ack(delivery_tag=method.delivery_tag)

    def process_gui_action_request_msg(self, ch, method, properties, body):
        # infinite loop of magical random numbers
        print(f"Received configuration request: {body}")
        input_form = user_interface.ui_reports.InputFormBody.build_from_json(body)

        # Check if device configuration is requested:
        if {"DevAddr", "DevEUI", "AppKey"}.issubset({field['name'] for field in input_form.fields}):
            device_credentials_reply.reply_to = properties.reply_to
            device_credentials_reply.correlation_id = properties.correlation_id
            socketio.emit('user_alerts', "<p>Enter DUT ABP Credentials</p>", namespace='/test')
            socketio.emit('enable_dut_button', "", namespace='/test')
        elif {"START"} == {field['name'] for field in input_form.fields}:
            start_reply.reply_to = properties.reply_to
            start_reply.correlation_id = properties.correlation_id
            socketio.emit('user_alerts', "<p>Press start after the Agent is running.</p>", namespace='/test')
            socketio.emit('enable_start_button', "", namespace='/test')

    def run(self):
        print("Starting consume.")
        self.mq_interface.consume_start()


@app.route('/')
def index():
    global refresh_count
    flask.flash(f"Reload count = {refresh_count}")
    refresh_count += 1

    # only by sending this page first will the client be connected to the socketio instance
    return flask.render_template('index.html')


@socketio.on('connect', namespace='/test')
def test_connect():
    # need visibility of the global thread object
    global thread
    print('Client connected')

    # Start the random number generator thread only if the thread has not been started before.
    if not thread.isAlive():
        print("Starting Thread")
        thread = UiListener()
        thread.start()


@socketio.on('get_device_from_gui', namespace='/test')
def send_dut_configuration(message):
    print("sending device information...")
    device_credentials_reply.body = json.dumps({"fields": [{"DevEUI": message['dev_eui']},
                                                           {"AppKey": message['app_key']},
                                                           {"DevAddr": message['dev_addr']}]})
    device_credentials_reply.send()


@socketio.on('start_button_pressed', namespace='/test')
def send_device_information(json):
    print("The start button was pressed...")
    start_reply.send()


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
