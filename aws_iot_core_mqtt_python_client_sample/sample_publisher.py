"""Publish a message to an MQTT topic"""
import json
from logging import DEBUG, basicConfig, getLogger
from os import path
from time import sleep
from uuid import uuid4

import click
from awscrt import mqtt
from awscrt.exceptions import AwsCrtError
from awsiot import mqtt_connection_builder

# certificate paths will be computed relative to current file dir
DIR_PATH = path.abspath(path.dirname(__file__))

# names of files that contain the relevant certificates
DEVICE_CERTIFICATE_FILENAME = "cert.pem"
DEVICE_KEY_FILENAME = "private.key"
AWS_ROOT_CA = "AmazonRootCA1.pem"

# setup logger
basicConfig(level=DEBUG)
LOG = getLogger(__name__)


def _new_mqtt_connection(
    aws_mqtt_endpoint: str,
    client_id: str,
    dev_pem_path: str,
    dev_private_key_path: str,
    root_ca_path: str,
):
    return mqtt_connection_builder.mtls_from_path(
        endpoint=aws_mqtt_endpoint,
        cert_filepath=dev_pem_path,
        pri_key_filepath=dev_private_key_path,
        ca_filepath=root_ca_path,
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
    help="Topic to publish to",
    default="test/commands",
)
@click.option(
    "--count",
    "-n",
    type=click.INT,
    help="Number of times to publish the message",
    default=1,
)
@click.option(
    "--cert-dir",
    "-C",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="Directory containing AWS IoT Core certificates",
    default=DIR_PATH,
)
@click.option(
    "--message",
    "-m",
    type=click.STRING,
    help="The actual message you want to publish on the MQTT topic",
)
def cli(endpoint, client_prefix, topic, count, cert_dir, message):
    """Publish a message to an MQTT topic on AWS IoT Core."""
    client_id = f"{client_prefix}-{uuid4()}"

    connection = _new_mqtt_connection(
        aws_mqtt_endpoint=endpoint,
        client_id=client_id,
        dev_pem_path=path.join(cert_dir, DEVICE_CERTIFICATE_FILENAME),
        dev_private_key_path=path.join(cert_dir, DEVICE_KEY_FILENAME),
        root_ca_path=path.join(cert_dir, AWS_ROOT_CA),
    )
    LOG.debug(
        "connecting to '%(endpoint)s' using client ID '%(client_id)s'",
        {"endpoint": endpoint, "client_id": client_id},
    )
    try:
        future = connection.connect()
        future.result()
        LOG.info("connected to '%s'", endpoint)
    except AwsCrtError as ace:
        LOG.fatal("could not connect to AWS IoT Core", exc_info=ace)
        return

    try:
        for i in range(1, count + 1):
            connection.publish(
                topic=topic,
                payload=message,
                qos=mqtt.QoS.AT_LEAST_ONCE,  # quality of service
            )
            LOG.debug(
                "published message #%(index)d on '%(topic)s'",
                {"index": i, "topic": topic},
            )
            sleep(1)
    except Exception as exc:  # pylint: disable=broad-except
        LOG.fatal("Error while p", exc_info=exc)
    finally:
        LOG.info("done")


if __name__ == "__main__":
    cli(auto_envvar_prefix="MQTT_PUBLISHER")
