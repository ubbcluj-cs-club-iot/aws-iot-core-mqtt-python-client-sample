import json
import click

from awscrt import mqtt
from awsiot import mqtt_connection_builder
from logging import basicConfig, getLogger, DEBUG
from os import path
from pprint import pprint
from signal import signal, SIGTERM, SIGINT
from threading import Event
from uuid import uuid4

# certificates are loaded relative to the current file's directory
DIR_PATH = path.abspath(path.dirname(__file__))

# names of files that contain the relevant certificates
DEVICE_CERTIFICATE_FILENAME = "device.pem"
DEVICE_KEY_FILENAME = "device_rsa"
AWS_ROOT_CA = "AmazonRootCA1.pem"

# setup logger
basicConfig(level=DEBUG)
LOG = getLogger(__name__)


# Callback when connection is accidentally lost.
def on_connection_interrupted(_, error, **kwargs):
    LOG.error("Connection interrupted", exc_info=error)


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    LOG.debug(
        "Connection resumed. return_code: {} session_present: {}".format(
            return_code, session_present
        )
    )

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        LOG.info(
            "Previous session did not persist. Resubscribing to existing topics..."
        )
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results["topics"]:
        if qos is None:
            exit("Server rejected resubscribe to topic: {}".format(topic))


def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    LOG.info("received message on topic %s", topic)
    pprint(json.loads(payload))


def new_mqtt_connection(
    client_id: str,
    dev_cert_filename: str,
    dev_key_filename: str,
    ca_filename: str,
    aws_mqtt_endpoint: str,
):
    return mqtt_connection_builder.mtls_from_path(
        endpoint=aws_mqtt_endpoint,
        cert_filepath=path.join(DIR_PATH, dev_cert_filename),
        pri_key_filepath=path.join(DIR_PATH, dev_key_filename),
        ca_filepath=path.join(DIR_PATH, ca_filename),
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id=client_id,
        clean_session=True,
        keep_alive_secs=10,
    )


def _connect(endpoint: str, client_prefix: str):
    try:
        client_id = f"{client_prefix}-{uuid4()}"
        LOG.debug(
            "Connecting to '%(endpoint)s using client ID '%(client_id)s'",
            {"endpoint": endpoint, "client_id": client_id},
        )

        connection = new_mqtt_connection(
            aws_mqtt_endpoint=endpoint,
            client_id=client_id,
            dev_cert_filename="device.pem",
            dev_key_filename="device_rsa",
            ca_filename="AmazonRootCA1.pem",
        )
        con_future = connection.connect()
        con_future.result()

        LOG.info("Connected.")
        return connection
    except Exception as e:
        LOG.fatal("Couldn't connect to MQTT endpoint", exc_info=e)
        return False


def _subscribe(connection, topic):
    LOG.debug("Subscribing to topic '%(topic)s' ...", {"topic": topic})
    try:
        subscribe_future, _ = connection.subscribe(
            topic=topic, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_message_received
        )
        result = subscribe_future.result()
        LOG.info(
            "Subscribed to %(topic)s with %(qos)s.",
            {"topic": topic, "qos": result["qos"]},
        )
    except Exception as e:
        LOG.exception("Failed to subscribe to topic", exc_info=e)


def _disconnect(connection):
    LOG.info("Disconnecting from MQTT broker")
    try:
        con_future = connection.disconnect()
        con_future.result()
        LOG.info("Disconnected.")
    except Exception as e:
        LOG.exception("Failed to disconnect properly", exc_info=e)


@click.command()
@click.option(
    "--endpoint", "-e", type=click.STRING, help="AWS MQTT endpoint for your thing"
)
@click.option(
    "--client-prefix",
    "-p",
    type=click.STRING,
    help="Prefix the client ID with this string",
    default="test",
)
@click.option(
    "--topic",
    "-t",
    type=click.STRING,
    help="Topic to subscribe to",
    default="test/commands",
)
def cli(endpoint, client_prefix, topic):
    _STOP = Event()

    def _stop_program(_, __):
        nonlocal _STOP
        if not _STOP.is_set():
            _STOP.set()

    signal(SIGINT, _stop_program)
    signal(SIGTERM, _stop_program)
    LOG.info("Subscriber sample. Hit Ctrl-C to exit.")

    connection = _connect(endpoint, client_prefix)
    if not connection:
        return
    _subscribe(connection, topic)
    _STOP.wait()
    _disconnect(connection)


if __name__ == "__main__":
    cli(auto_envvar_prefix="MQTT_SUBSCRIBER")
