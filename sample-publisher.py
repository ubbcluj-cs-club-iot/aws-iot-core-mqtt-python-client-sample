import click
import json

from awscrt import mqtt
from awsiot import mqtt_connection_builder
from logging import basicConfig, getLogger, DEBUG
from os import path
from random import random
from time import sleep
from uuid import uuid4


# certificate paths will be computed relative to current file dir
DIR_PATH = path.abspath(path.dirname(__file__))

# names of files that contain the relevant certificates
DEVICE_CERTIFICATE_FILENAME = "device.pem"
DEVICE_KEY_FILENAME = "device_rsa"
AWS_ROOT_CA = "AmazonRootCA1.pem"

# setup logger
basicConfig(level=DEBUG)
LOG = getLogger(__name__)


def new_mqtt_connection(
    aws_mqtt_endpoint: str,
    client_id: str,
    dev_cert_filename: str,
    dev_key_filename: str,
    ca_filename: str,
):
    return mqtt_connection_builder.mtls_from_path(
        endpoint=aws_mqtt_endpoint,
        cert_filepath=path.join(DIR_PATH, dev_cert_filename),
        pri_key_filepath=path.join(DIR_PATH, dev_key_filename),
        ca_filepath=path.join(DIR_PATH, ca_filename),
        client_id=client_id,
        clean_session=True,
        keep_alive_secs=10,
    )


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
@click.option(
    "--count",
    "-n",
    type=click.INT,
    help="Number of messages to publish",
    default=10
)
def cli(endpoint, client_prefix, topic, count):
    client_id = f"{client_prefix}-{uuid4()}"
    connection = new_mqtt_connection(
        aws_mqtt_endpoint=endpoint,
        client_id=client_id,
        dev_cert_filename=DEVICE_CERTIFICATE_FILENAME,
        dev_key_filename=DEVICE_KEY_FILENAME,
        ca_filename=AWS_ROOT_CA,
    )
    LOG.debug(
        "connecting to '%(endpoint)s using client ID '%(client_id)s'",
        {"endpoint": endpoint, "client_id": client_id},
    )
    try:
        future = connection.connect()
        future.result()
        LOG.info("connected")

        for i in range(1, count+1):
            rand = random()
            temperature = 23.0 - rand if (i % 2) == 0 else 23.0 + rand
            humidity = 150.0 + 3.14 * rand
            connection.publish(
                topic=topic,
                payload=json.dumps({"temperature": temperature, "humidity": humidity}),
                qos=mqtt.QoS.AT_LEAST_ONCE,  # quality of service
            )
            LOG.debug(
                "published message #%(index)d on '%(topic)s",
                {"index": i, "topic": topic},
            )
            sleep(1)
    except Exception as e:
        LOG.fatal("AWS IoT publish failed!", exc_info=e)
    finally:
        LOG.info("done")


if __name__ == "__main__":
    cli()
