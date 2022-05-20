# AWS IoT Core Connection Sample

This is derived from the AWS IoT SDK for Python v2 samples.
It's more inlined, so we understand more quickly what a quick
IoT Core connection entails rather than learn the DSL of the
AWS samples.

# Running

Both scripts have instructions that you can read by running them
with the `--help` argument.

Both of these scripts require placing the following files in the
same directory where the scripts are located:

* `device_rsa` - the device's private key - typically generated
  when creating a new AWS IoT Core thing
* `device.pem` - the device's certificate - typically generated
  when creating a new AWS IoT Core thing
* `AmazonRootCA1.pem` - Amazon [root certificate](https://www.amazontrust.com/repository/AmazonRootCA1.pem)

## Publisher

Publishes fake temperature and humidity readings. A basic call to
this script looks like this:

```shell
python sample-publisher.py \
    --endpoint "<prefix>-ats.iot.<region>.amazonaws.com
    --client-prefix "some-client-id-prefix-your-certificate-has-access-to"
    --topic "some-topic-your-certificate-has-access-to"
    --count "number-of-messages-to-publish"
```

## Subscriber

Prints out whatever comes in through the topics matching the specified
topic filter. Supports reconnecting in case of connection interruption.

```shell
python sample-publisher.py \
    --endpoint "<prefix>-ats.iot.<region>.amazonaws.com
    --client-prefix "some-client-id-prefix-your-certificate-has-access-to"
    --topic "some-topic-filter-your-certificate-has-access-to"
```
