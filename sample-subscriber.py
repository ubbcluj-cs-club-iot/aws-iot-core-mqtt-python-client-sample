from awscrt import mqtt
from awsiot import mqtt_connection_builder
from logging import basicConfig, getLogger, DEBUG
from os import path
from pprint import pprint
from signal import signal, SIGTERM, SIGINT
from threading import Event
from uuid import uuid4

# specify some default values
MQTT_ENDPOINT = "a3pdeg88222nmq-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = f"4esttech-device-client-{uuid4()}"
TOPIC_NAME = "4esttech/device-commands"
DIR_PATH = path.abspath(path.dirname(__file__))

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


if __name__ == "__main__":
    _STOP = Event()

    def _stop_program(_, __):
        global _STOP
        if not _STOP.is_set():
            _STOP.set()

    signal(SIGINT, _stop_program)
    signal(SIGTERM, _stop_program)

    connection = new_mqtt_connection(
        aws_mqtt_endpoint=MQTT_ENDPOINT,
        client_id=CLIENT_ID,
        dev_cert_filename="device.pem",
        dev_key_filename="device_rsa",
        ca_filename="AmazonRootCA1.pem",
    )
    LOG.info("Subscriber sample. Hit Ctrl-C to exit.")

    LOG.debug(
        "connecting to '%(endpoint)s using client ID '%(client_id)s'",
        {"endpoint": MQTT_ENDPOINT, "client_id": CLIENT_ID},
    )
    try:
        con_future = connection.connect()
        con_future.result()
        LOG.info("connected")
        LOG.debug("Subscribing to topic '%(topic)s' ...", {"topic": TOPIC_NAME})

        subscribe_future, packet_id = connection.subscribe(
            topic=TOPIC_NAME, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_message_received
        )
        result = subscribe_future.result()
        LOG.debug("subscribed with %(qos)s.", {"qos": result["qos"]})

        _STOP.wait()  # wait here until someone hits Ctrl-C

        con_future = connection.disconnect()
        con_future.result()
        LOG.info("Disconnected.")

    except Exception as e:
        LOG.fatal("AWS IoT publish failed!", exc_info=e)
    finally:
        LOG.info("done")
