import base64
import time
import json
import struct

import lorawan.flora_agent.messenger.mock_parsing
import lorawan.flora_agent.messenger.mock_sessions as mock_sessions
import lorawan.sessions
import message_queueing
import lorawan.lorawan_parameters.general
import lorawan.lorawan_parameters.testing
import lorawan.parsing.lorawan
import lorawan.parsing.flora_messages
import parameters.message_broker as message_broker
import utils
import lorawan.lorawan_utils
from parameters.message_broker import routing_keys
from user_interface.ui_reports import API_VERSION
last_sent = 0


class MessageGenerator(object):
    """
    This class mocks the end node and the gateway with the packet forwarder.
    """

    def __init__(self, config_dev_dict, conf_testserver_dict):
        self.node = mock_sessions.EndDeviceMock(deveui=base64.b64decode(config_dev_dict["DevEUI"]),
                                                devaddr=base64.b64decode(config_dev_dict["DevAddr"]),
                                                appkey=base64.b64decode(config_dev_dict["AppKey"]),
                                                appskey=base64.b64decode(config_dev_dict["AppSKey"]),
                                                nwkskey=base64.b64decode(config_dev_dict["NwkSKey"]))
        self.testserver_config = conf_testserver_dict
        self.mqif = message_queueing.MqInterface()
        self.last_pong_request = lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG
        self.__last_freq_idx = 0

        self.mqif.declare_and_consume(queue_name='down_nwk_mock',
                                      routing_key=message_broker.routing_keys.toAgent+'.#',
                                      callback=self.handle_nwk_down_msg)

        self.mqif.declare_and_consume(queue_name='mock_up_message_actok',
                                      routing_key='mock.up.message.actok',
                                      callback=self.handle_mock_up_message_actok)

        self.mqif.declare_and_consume(queue_name='mock_up_message_pong',
                                      routing_key='mock.up.message.pong',
                                      callback=self.handle_mock_up_message_pong)

        self.mqif.declare_and_consume(queue_name='mock_up_message_join',
                                      routing_key='mock.up.message.join',
                                      callback=self.handle_mock_up_message_join)

        self.mqif.declare_and_consume(queue_name='mock_up_data',
                                      routing_key='mock.up.data',
                                      callback=self.handle_mock_up_data)

        self.mqif.declare_and_consume(queue_name='mock_configure',
                                      routing_key='mock.configure',
                                      callback=self.handle_mock_configure_node)

        self.mqif.declare_and_consume(queue_name='mock_configure_resetABP',
                                      routing_key='mock.configure.resetABP',
                                      callback=self.handle_mock_configure_node_resetabp)

        self.mqif.declare_and_consume(queue_name='mock_configure_showinfo',
                                      routing_key='mock.configure.showinfo',
                                      callback=self.handle_mock_configure_showinfo)

        self.mqif.declare_and_consume(queue_name='mock_nwk_configure',
                                      routing_key='mock.nwk.configure',
                                      callback=self.handle_mock_nwk_configure)

        self.mqif.declare_and_consume(queue_name='mock_coordinate_start',
                                      routing_key='mock.testsuite.start',
                                      callback=self.handle_mock_test_start)

        self.mqif.declare_and_consume(queue_name='mock_testsuite_terminate',
                                      routing_key='mock.testsuite.terminate',
                                      callback=self.handle_mock_terminate)

    def get_frequency(self):
        freq = self.node.loramac_params.channel_struct.used_frequencies[
            self.__last_freq_idx % len(self.node.loramac_params.channel_struct.used_frequencies)]
        self.__last_freq_idx += 1
        return freq

    def start_consuming(self):
        self.mqif.consume_start()

    def handle_mock_up_data(self, ch, method, properties, body):
        print("Processing data message from cli.", flush=True)
        cli_message = lorawan.flora_agent.messenger.mock_parsing.MockMessage(json_mockmsg_str=body.decode())
        print(cli_message, flush=True)
        print("FPort: {0}".format(cli_message.get_fport()), flush=True)
        print("FRMPayload: {0}\n\n".format(cli_message.get_frmpayload_bytes()), flush=True)
        if cli_message.is_confirmed():
            mac_header = lorawan.lorawan_parameters.general.MHDR.CONFIRMED_UP
        else:
            mac_header = lorawan.lorawan_parameters.general.MHDR.UNCONFIRMED_UP
        self.send_to_testing_tool(
            broker_channel=ch,
            payload=cli_message.get_frmpayload_bytes(),
            mhdr=mac_header,
            port=cli_message.get_fport(),
            fctrl=lorawan.lorawan_utils.get_fctrl_up_byte(ack=False,
                                                          adrackreq=False,
                                                          adr=False,
                                                          foptlen=len(cli_message.get_fopts_bytes())),
            fopts=cli_message.get_fopts_bytes())

    def handle_mock_configure_node(self, ch, method, properties, body):
        print("Processing configuration request", flush=True)
        cli_message = lorawan.flora_agent.messenger.mock_parsing.MockMessage(json_mockmsg_str=body.decode())
        print(cli_message)
        print("use_dr: {0}".format(cli_message.get_use_dr()), flush=True)
        print("freq: {0}\n\n".format(cli_message.get_freq()), flush=True)
        self.node.loramac_params.rx1_dr_offset = getattr(lorawan.lorawan_parameters.general.LORA_DR,
                                                         cli_message.get_use_dr())
        self.node.add_frequency(cli_message.get_freq())

    def handle_mock_configure_node_resetabp(self, ch, method, properties, body):
        print("Reseting keys to the assigned for ABP.", flush=True)
        self.node.reset_apb_keys()

    def handle_mock_configure_showinfo(self, ch, method, properties, body):
        print("\nNode Session Information:", flush=True)
        print(self.node, flush=True)

    def handle_mock_up_message_actok(self, ch, method, properties, body):
        payload = struct.pack('>H', self.node.download_counter)
        self.send_to_testing_tool(broker_channel=ch,
                                  payload=payload,
                                  port=224)

    def handle_mock_up_message_pong(self, ch, method, properties, body):
        pong = lorawan.lorawan_utils.generate_pingpong(ping=self.last_pong_request)[1]
        self.send_to_testing_tool(broker_channel=ch,
                                  payload=pong,
                                  port=224)
        print("Pong sent: {0}\n\n".format(utils.bytes_to_text(pong)), flush=True)

    def handle_mock_up_message_join(self, ch, method, properties, body):
        join_request = self.node.get_join_request(appeui=base64.b64decode(self.testserver_config["AppEUI"]))
        self.send_to_testing_tool(broker_channel=ch,
                                  payload=join_request,
                                  mhdr=lorawan.lorawan_parameters.general.MHDR.JOIN_REQUEST)
        print("Join Request Sent.", flush=True)
        print(join_request, flush=True)
        print("\n\n", flush=True)

    def handle_nwk_down_msg(self, ch, method, properties, body):
        nwk_message = lorawan.parsing.flora_messages.GatewayMessage(json_ttm_str=body.decode())
        phypayload = nwk_message.get_phypaload_bytes()
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", flush=True)
        global last_sent
        print("Time since last uplink message sent: {} s.".format(time.time() - last_sent))
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", flush=True)
        print("New message received.", flush=True)
        print("TMST: {}\n".format(nwk_message.tmst))
        print("FREQ: {}\n".format(nwk_message.freq))
        print("DATR: {}\n".format(nwk_message.datr))
        if phypayload[0:1] == lorawan.lorawan_parameters.general.MHDR.JOIN_ACCEPT:
            print("Join accept received, updating session.", flush=True)
            print("OLD IDENTIFICATION:", flush=True)
            print(self.node, flush=True)
            self.node.parse_join_accept(phypayload)
            print("NEW IDENTIFICATION:", flush=True)
            print(self.node, flush=True)
        else:
            lw_msg = nwk_message.parse_lorawan_message()

            rcv_pay = utils.encrypt_ieee802154(key=self.node.loramac_params.appskey,
                                               frmpayload=lw_msg.macpayload.frmpayload_bytes,
                                               direction=1,
                                               devaddr=lw_msg.macpayload.fhdr.devaddr_bytes,
                                               fcnt=lw_msg.macpayload.fhdr.get_fcnt_int())
            print(lw_msg, flush=True)
            print("Decrypted payload: {0}".format(utils.bytes_to_text(rcv_pay)), flush=True)
            print(rcv_pay, flush=True)

            if lw_msg.macpayload.fport_int == 224:  # Testing message detected
                self.node.download_counter += 1
                if rcv_pay == lorawan.lorawan_parameters.testing.FRMPAYLOAD.TEST_ACT:
                    print("Test Activation detected", flush=True)
                    self.node.download_counter = 0
                elif rcv_pay[0:1] == lorawan.lorawan_parameters.testing.TEST_CODE.PINGPONG:
                    self.last_pong_request = rcv_pay
                    print("Pong requested", flush=True)
                elif rcv_pay[0:1] == lorawan.lorawan_parameters.testing.TEST_CODE.TRIGGER_JOIN:
                    print("Join Request Triggered. Update session with a Join Request message.", flush=True)

    def handle_mock_nwk_configure(self, ch, method, properties, body):
        if body:
            test_list = body.decode().split()
        else:
            test_list = ["td_lorawan_act_01",
                         "td_lorawan_fun_01",
                         "td_lorawan_act_02",
                         "td_lorawan_end_loop"]
        config = {
                "_api_version": API_VERSION,
                "configuration": {
                    "testsuite.testcases": test_list
                },
                "session_id": "666",
                "testing_tools": "f-interop/flora",
                "users": ["user1"],
                "device_personalization": {
                        "DevAddr": "JgEQGA==",  # "ASgpnw==" 0128299f
                        "DevEUI": "OTAyNXY3ewQ=",  # "AASjCwAa2+U=",
                        "AppKey": "K34VFiiu0qar9xWICc9PPA==",
                        "AppSKey": "K34VFiiu0qar9xWICc9PPA==",
                        "NwkSKey": "K34VFiiu0qar9xWICc9PPA=="
                }
        }
        print("Sending session configuration.\n", flush=True)
        ch.basic_publish(body=json.dumps(config),
                         routing_key=routing_keys.session_configuration,
                         exchange=message_queueing.DEFAULT_EXCHANGE)

    def handle_mock_test_start(self, ch, method, properties, body):
        print("Starting Testing Tool.\n", flush=True)
        ch.basic_publish(body="",
                         routing_key=message_broker.routing_keys.testing_start,
                         exchange=message_queueing.DEFAULT_EXCHANGE)

    def handle_mock_terminate(self, ch, method, properties, body):
        print("Terminating Testing Tool.\n", flush=True)
        ch.basic_publish(body="",
                         routing_key=message_broker.routing_keys.testing_terminate,
                         exchange=message_queueing.DEFAULT_EXCHANGE)

    def send_to_testing_tool(self, broker_channel, payload,
                             port=None,
                             mhdr=lorawan.lorawan_parameters.general.MHDR.UNCONFIRMED_UP,
                             fctrl=lorawan.lorawan_parameters.general.FCTRL.UP_ADROFF_ADRACKOFF_ACKOFF_FOPTLEN0,
                             fopts=b''):
        """
        Creates a Gateway Message to send the payload to the Testing Tool. This payload could be the FRMPayload
        of a data messages (plain text to be encrypted) or a join request including the MIC and MHDR.

        PRECONDITION: In case of data messages a port must be provided.
        :param broker_channel:
        :param payload: bytes of FRMPayload in plain text for data messages and PHYPayload for Join Requests.
        :param port: int indicating the port. Must be provided for data messages.
        :param mhdr: MAC header of the message being sent.
        :param fctrl: Frame control field (FCtrl) of the frame header (FHDR).
        :param fopts: Optional frame options field (FOpts) of the frame header (FHDR).
        :return: None
        """
        print("Sending message to testing tool", flush=True)
        print("FRMPayload plain text: {0}".format(utils.bytes_to_text(payload)), flush=True)
        if mhdr == lorawan.lorawan_parameters.general.MHDR.JOIN_REQUEST:
            phypayload = payload
        else:
            assert port is not None
            phypayload = self.node.prepare_lorawan_data(frmpayload=payload,
                                                        fport=port,
                                                        mhdr=mhdr,
                                                        fctr=fctrl,
                                                        fopts=fopts)
        print("PHYPayload: {0}\n".format(utils.bytes_to_text(phypayload)), flush=True)
        ulmsg = lorawan.parsing.flora_messages.GatewayMessage()
        ulmsg.data = base64.b64encode(phypayload).decode()
        ulmsg.size = len(phypayload)
        ulmsg.freq = self.get_frequency()
        ulmsg.tmst = round(time.time())
        ulmsg.datr = self.node.loramac_params.default_dr
        global last_sent
        last_sent = time.time()
        print(str(ulmsg))
        broker_channel.basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                     routing_key=message_broker.routing_keys.fromAgent+'.gw1',
                                     body=str(ulmsg))
