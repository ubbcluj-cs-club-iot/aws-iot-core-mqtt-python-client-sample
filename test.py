from awsiot import mqtt_connection_builder
from os import path


DIR_PATH = path.abspath(path.dirname(__path__))


def on_connection_interrupted(*args):
    print(args)


def on_connection_resumed(*args):
    print(args)


def new_mqtt_connection(client_id: str, cert_path: str, key_path: str, ca_path: str):
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint="a3pdeg88222nmq-ats.iot.us-east-1.amazonaws.com",
        cert_filepath=path.join(DIR_PATH, "device.pem"),
        pri_key_filepath=path.join(DIR_PATH, "device_rsa"),
        ca_filepath=path.join(DIR_PATH, "AmazonRootCA1.pem"),
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        client_id="4esttech-device-client",
        clean_session=True,
        keep_alive_secs=10,
    )
