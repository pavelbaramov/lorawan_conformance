import os
import click
import json
import pika
import pika.exceptions
import base64
import copy
import lorawan.lorawan_parameters.general
import message_queueing


default_ulr = os.environ.get('AMQP_URL')
connection_params = pika.URLParameters(default_ulr)
try:
    connection = pika.BlockingConnection(connection_params)
except pika.exceptions.ConnectionClosed as conn_closed:
    connection = None

empty_mock_msg = {
    'use_dr': 0,
    'freq': 868.5,
    'frmpayload': '',
    'port': 1,
    'fopts': '',
    'confirmed': False,
}


def get_channel(rmq_url=None):
    global connection
    global connection_params
    global default_ulr
    if rmq_url:
        params = pika.URLParameters(rmq_url)
        connection = pika.BlockingConnection(params)
    try:
        channel = connection.channel()
    except pika.exceptions.ConnectionClosed:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
    return channel


def validate_frmpayload(ctx, param, frmpayload_str):
    try:
        frmpayload_bytes = bytes.fromhex(frmpayload_str)
        return frmpayload_bytes
    except ValueError:
        raise click.BadParameter('Bad Frame Payload (e.g. 04ff0201).')


def validate_fopts(ctx, param, fopts):
    try:
        fopts_bytes = bytes.fromhex(fopts)
        return fopts_bytes
    except ValueError:
        raise click.BadParameter('Bad Frame Payload (e.g. 02).')


@click.command()
@click.option('--frmpayload', callback=validate_frmpayload, default="ffffffffff", type=str,
              help='bytes to be sent (e.g. 01af02). Default: ffffffffff')
@click.option('--fopts', callback=validate_fopts, default="", type=str,
              help='Bytes of the FOpts fiedl of the FHDR (e.g. 02). Empty by default')
@click.option('--fport', default=2, type=click.IntRange(0, 255, clamp=False),
              help="Integer value of the desired port (e.g. 224). Default value: 2")
@click.option('--use_confirmed',
              default=False,
              is_flag=True,
              help='Flag that indicates to use a confirmed message. Default: False (Unconfirmed)')
def send(frmpayload, fopts, fport, use_confirmed):
    """Command used to send data or MAC commands in the frmpayload of a lorawan message."""
    global empty_mock_msg
    click.echo("FRMPayload: {0}".format(frmpayload))
    click.echo("FPort: {0}".format(fport))
    click.echo("FOpts: {0}".format(fopts))
    click.echo("Use confirmed: {0}".format(use_confirmed))
    mockmsg = copy.copy(empty_mock_msg)
    mockmsg["frmpayload"] = base64.b64encode(frmpayload).decode()
    mockmsg["fopts"] = base64.b64encode(fopts).decode()
    mockmsg["port"] = fport
    if use_confirmed:
        mockmsg["confirmed"] = True
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.up.data',
                                body=json.dumps(mockmsg))


# noinspection PyProtectedMember
def validate_use_dr(ctx, param, use_dr):
    if use_dr not in lorawan.lorawan_parameters.general.LORA_DR._asdict().keys():
        raise click.BadParameter("Invalid LoRa Data Rate (DR).")
    return use_dr


def validate_freq(ctx, param, freq):
    if freq not in lorawan.lorawan_parameters.general.MIN_LORA_FREQ:
        raise click.BadParameter("Invalid LoRa frequency for this Region.")
    return freq


@click.command()
@click.option('--freq', callback=validate_freq, default=868.1, type=float,
              help="Adds this frequency to be used (e.g. 868.3). Default: 868.1.")
@click.option('--use_dr', callback=validate_use_dr, default='DR0', type=str,
              help="Set the data rate (e.g. DR2). Default: DR0.")
@click.option('--reset_abp_keys',
              default=False,
              is_flag=True,
              help='Reset the keys and device address to the ABP values.')
def configure_device_mock(freq, use_dr, reset_abp_keys):
    """Use this command to configure the lorawan_parameters of the end device mock."""
    click.echo("Configuring")
    click.echo("freq: {0}".format(freq))
    click.echo("Data Rate: {0}".format(use_dr))
    mockmsg = copy.copy(empty_mock_msg)
    mockmsg["use_dr"] = use_dr
    mockmsg["freq"] = freq
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.configure',
                                body=json.dumps(mockmsg))
    if reset_abp_keys:
        get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                    routing_key='mock.configure.resetABP',
                                    body="")


@click.command()
def show_info():
    """ Use this command to print the end device mock information in the agent."""
    click.echo("Requesting mock device session information.")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.configure.showinfo',
                                body="")


@click.command()
def send_actok():
    """ Sends an Activation OK message to the testing tool."""
    click.echo("Sending ACT OK")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.up.message.actok',
                                body="")


def validate_test_list(ctx, param, test_list_str):
    name_list = test_list_str.split()
    valid_names = ['act_01',
                   'act_02',
                   'act_03',
                   'act_04',
                   'fun_01',
                   'fun_02',
                   'fun_03',
                   'end_loop']
    test_list = []
    for name in name_list:
        if name not in valid_names:
            raise click.BadParameter("Invalid Test Name: {}.".format(name))
        else:
            test_list.append("td_lorawan_"+name)
    return " ".join(test_list)


@click.command()
@click.option('--tests', callback=validate_test_list, default="", type=str,
              help="List of the tests to be executed as a string with the name of the tests separated with a space.")
def send_session_config(tests):
    """ Sends the session configuration information to the testing tool, specifying the test list."""
    click.echo("Sending Configuration to Testing Tool.")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.nwk.configure',
                                body=tests)


@click.command()
def send_test_start():
    """ Starts the testing tool."""
    click.echo("Starting Testing Tool.")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.testsuite.start',
                                body="")


@click.command()
def send_terminate():
    """ Starts the testing tool."""
    click.echo("Terminating Testing Tool.")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.testsuite.terminate',
                                body="")


@click.command()
def send_join():
    """Sends a join request message to the testing tool."""
    click.echo("Sending Join Accept")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.up.message.join',
                                body="")


@click.command()
def send_pong():
    """Sends a the PONG response of the last received PING to the testing app."""
    click.echo("Sending PONG")
    get_channel().basic_publish(exchange=message_queueing.DEFAULT_EXCHANGE,
                                routing_key='mock.up.message.pong',
                                body="")
