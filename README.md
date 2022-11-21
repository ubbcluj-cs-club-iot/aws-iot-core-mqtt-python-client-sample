# AWS IoT Core Connection Sample

This is derived from the AWS IoT SDK for Python v2 samples.
It's more inlined, so we understand more quickly what a quick
IoT Core connection entails rather than learn the DSL of the
AWS samples.

# Running

Both scripts have instructions that you can read by running them
with the `--help` argument.

Both of these scripts require placing the following files in the
a directory on the device where the scripts are located:

* `private.key` - the device's private key - typically generated
  when creating a new AWS IoT Core thing
* `cert.pem` - the device's certificate - typically generated
  when creating a new AWS IoT Core thing
* `AmazonRootCA1.pem` - Amazon [root certificate](https://www.amazontrust.com/repository/AmazonRootCA1.pem)

AWS IoT Core uses the above certificates to identify the device as
an AWS IoT Core Thing and secure the communication between the device
and AWS IoT Core. AWS IoT Core assigns various authorization levels
based on the identity inferred from the certificates via policies.

Both of the scripts allow specifying the location of the certificates
via the `-C` option.
## Publisher

The sample publisher script allows publishing a message up to N times
over an MQTT connection.

```shell
$ python aws_iot_core_mqtt_python_client_sample/sample_publisher.py \
    -e "<prefix>-ats.iot.<region>.amazonaws.com \
    -p "some-client-id-prefix-your-certificate-has-access-to" \
    -t "some-topic-your-certificate-has-access-to" \
    -n "number-of-messages-to-publish" \
    -C "directory-where-the-certificates-are-stored" \
    -m "message to publish"
```

The `-p` option is used to construct the client ID of the publisher.
Clients use TLS certificates to connect to AWS IoT Core. A certificate is
typically granted the `iot:Connect` permission only for certain client IDs.
If this permission was granted for a specific client ID, use that ID. If it
was granted for a wildcard (indicated by the presence of `*`) then use the
common prefix for the wildcard client IDs.

The `-t` option specifies the MQTT topic where the script should publish
the message. As with the client ID, make sure that the script's TLS certificate
has the `iot:Publish` permission on the specified topic.

To see what permissions are assigned to a device certificate, see the
[IoT Policy Hub](https://us-east-1.console.aws.amazon.com/iot/home?region=us-east-1#/policyhub)
in the AWS IoT Core console.

The script allows loading the device certificates from a custom location via
the `-C` option.
## Subscriber

Prints out whatever comes in through the topics matching the specified
topic filter. Supports reconnecting in case of connection interruption.

```shell
$ python aws_iot_core_mqtt_python_client_sample/sample_susbcriber.py \
    -e "<prefix>-ats.iot.<region>.amazonaws.com \
    -p "some-client-id-prefix-your-certificate-has-access-to" \
    -t "some-topic-filter-your-certificate-has-access-to" \
    -C "directory-containing-the-IoT-Thing-certificates"
```

As with the publisher, the subscriber needs a client prefix it has access
to and a topic it can `iot:Subscribe` to. What those are is dependent on
the device certificates that the subscriber script uses.
