import json

from awscrt import mqtt
from awsiot import mqtt_connection_builder
from logging import basicConfig, getLogger, DEBUG
from os import path
from random import random
from time import sleep
from uuid import uuid4

# specify some default values
MQTT_ENDPOINT = "a3pdeg88222nmq-ats.iot.us-east-1.amazonaws.com"
CLIENT_ID = f"4esttech-device-client-{uuid4()}"
TOPIC_NAME = "4esttech/device-messages"
DIR_PATH = path.abspath(path.dirname(__file__))

# setup logger
basicConfig(level=DEBUG)
LOG = getLogger(__name__)


def on_connection_interrupted(*args):
    print(args)


def on_connection_resumed(*args):
    print(args)


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
    connection = new_mqtt_connection(
        aws_mqtt_endpoint=MQTT_ENDPOINT,
        client_id=CLIENT_ID,
        dev_cert_filename="device.pem",
        dev_key_filename="device_rsa",
        ca_filename="AmazonRootCA1.pem",
    )
    LOG.debug(
        "connecting to '%(endpoint)s using client ID '%(client_id)s'",
        {"endpoint": MQTT_ENDPOINT, "client_id": CLIENT_ID},
    )
    try:
        future = connection.connect()
        future.result()
        LOG.info("connected")

        for i in range(1, 10):
            rand = random()
            temperature = 23.0 - rand if (i % 2) == 0 else 23.0 + rand
            humidity = 150.0 + 3.14 * rand
            connection.publish(
                topic=TOPIC_NAME,
                payload=json.dumps({"temperature": temperature, "humidity": humidity}),
                qos=mqtt.QoS.AT_LEAST_ONCE,  # quality of service
            )
            LOG.debug(
                "published message #%(index)d on '%(topic)s",
                {"index": i + 1, "topic": TOPIC_NAME},
            )
            sleep(1)
    except Exception as e:
        LOG.fatal("AWS IoT publish failed!", exc_info=e)
    finally:
        LOG.info("done")
