"""
Main module of the test session. Each test session has a list of tests to be executed,
based in the test cases selected by the user.
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

import conformance_testing.test_errors as test_errors
from conformance_testing import testingtool_services
from user_interface.ui import ui_publisher
import parameters.message_broker as message_broker
import user_interface.ui_reports as ui_reports

from lorawan.lorawan_conformance import test_names

# Load all the modules of the available tests.
test_modules = dict()
for test_group in test_names.keys():
    for name in test_names[test_group]:
        test_modules[name] = __import__(
            "lorawan.lorawan_conformance."+test_group + '.' + name, globals(), locals(), ['object'])


def display_agent_tutorial(session_coordinator):
    """
    Auxiliary function to show instructions in the Graphical User Interface explaining how to download, configure
    and run the Agent application.
    :param session_coordinator: current session coordinator of the testing session.
    :return: None
    """
    agent_display = ui_reports.InputFormBody(title="Agent configuration tutorial.",
                                             tag_key="Agent",
                                             tag_value="Instructions")
    agent_display.add_field(ui_reports.ParagraphField(
        name="1-Verify you are using a compatible Python 3 version:",
        value='e.g. Python 3.5'))
    agent_display.add_field(ui_reports.ParagraphField(
        name="2-Install virtualenv:",
        value='e.g. pip install virtualenv'))
    agent_display.add_field(ui_reports.ParagraphField(
        name="3-Create a Python virtual environment:",
        value='e.g. virtualenv --python python3.5 venv'))
    agent_display.add_field(ui_reports.ParagraphField(
        name="4-Activate virtual environment:",
        value='e.g. source venv/bin/activate'))
    agent_display.add_field(ui_reports.ParagraphField(
        name="5-Install Agent:",
        value='e.g. pip install florawan_testing'))
    agent_display.add_field(ui_reports.ParagraphField(
        name="6-Configure the Packet Forwarder on the LoRa Gateway.:",
        value='e.g. set the UDP port and the IP on local.conf configuration file'))
    agent_display.add_field(ui_reports.ParagraphField(
        name="7-Set AMQP Broker URL:",
        value='e.g.: export AMQP_URL="'+session_coordinator.amqp_url+'"'))
    agent_display.add_field(ui_reports.ParagraphField(
        name="8-Set the IP of the interface listening to the Gateway with the Packet Forwarder (see step 6): ",
        value='e.g.: export PF_IP="XXX.XXX.XXX.XXX"'))
    agent_display.add_field(ui_reports.ParagraphField(
        name="9-Set Packet Forwarder UDP PORT (LoRa Gateway UDP Port): ",
        value='e.g.: export PF_UDP_PORT="XXXX"'))
    ui_publisher.display_on_gui(msg_str=str(agent_display),
                                key_prefix=message_broker.service_names.test_session_coordinator)


def testing_app_main():
    test_session_coordinator = testingtool_services.TestSessionCoordinator()
    while test_session_coordinator.testingtool_on:

        ui_publisher.testingtool_log(msg_str="\nWaiting for configuration.",
                                     key_prefix=message_broker.service_names.test_session_coordinator)
        # >> Display agent instructions: -----------------------------------------------------------------
        display_agent_tutorial(session_coordinator=test_session_coordinator)
        # << End agent instructions: --------------------------------------------------------------------
        test_session_coordinator.ask_configuration_register_device()
        test_session_coordinator.wait_press_start()
        result_report = ui_reports.InputFormBody(title="Results summary of the tests.",
                                                 tag_key="Test",
                                                 tag_value="Results")
        try:
            # for test_name in test_session_coordinator.requested_tests:
            while test_session_coordinator.test_available():
                try:
                    try:
                        test_name = test_session_coordinator.pop_next_test_name()
                        test_module = test_modules[test_name]
                    except KeyError:
                        raise test_errors.UnknownTestError(test_name)

                    ui_publisher.testingtool_log(msg_str="Selected test: {0}".format(test_name),
                                                 key_prefix=message_broker.service_names.test_session_coordinator)

                    test_session_coordinator.current_test = test_module.TestAppManager(test_session_coordinator)
                    ui_publisher.testingtool_log(msg_str="Test manager loaded: {}".format(test_name),
                                                 key_prefix=message_broker.service_names.test_session_coordinator)
                    test_session_coordinator.start_testing()
                ########################################################################
                # Catch Level 3 Errors
                ########################################################################
                except test_errors.TimeOutError as timeout_exception:
                    test_session_coordinator.handle_error(raised_exception=timeout_exception,
                                                          test_name=test_name,
                                                          result_report=result_report)

                ########################################################################
                # Catch Level 2 Errors
                ########################################################################
                except test_errors.TestFailError as test_fail_exception:
                    test_session_coordinator.handle_error(raised_exception=test_fail_exception,
                                                          test_name=test_name,
                                                          result_report=result_report)

                except test_errors.UnknownTestError as unknown_test:
                    test_session_coordinator.handle_error(raised_exception=unknown_test,
                                                          test_name=test_name,
                                                          result_report=result_report)

                except test_errors.SessionTerminatedError as session_terminated:
                    test_session_coordinator.handle_error(raised_exception=session_terminated,
                                                          test_name=test_name,
                                                          result_report=result_report)

                    break
                else:
                    result_report.add_field(ui_reports.ParagraphField(name=test_name, value="PASS"))
                finally:
                    test_session_coordinator.consume_stop()

        finally:
            test_session_coordinator.consume_stop()
            test_session_coordinator.channel.close()
            if not result_report.level == ui_reports.LEVEL_ERR:
                result_report.level = ui_reports.LEVEL_HL
                result_report.add_field(ui_reports.ParagraphField(name="TEST VERDICT: PASS", value=" "))
            else:
                result_report.add_field(ui_reports.ParagraphField(name="TEST VERDICT: FAIL", value=" "))

            ui_publisher.display_on_gui(msg_str=str(result_report),
                                        key_prefix=message_broker.service_names.test_session_coordinator)
            test_session_coordinator.testingtool_on = False


if __name__ == '__main__':
    testing_app_main()
