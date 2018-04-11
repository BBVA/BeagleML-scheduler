"""
Copyright 2018 Banco Bilbao Vizcaya Argentaria, S.A.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
"""Module for send messages in kafka."""
from confluent_kafka import Producer

import logging


class KafkaProducer:
    """Manages the communication with kafka."""

    def __init__(self, server, queue):
        """Init function."""
        self.logger = logging.getLogger("SCHEDULER")
        self.producer = Producer({'bootstrap.servers': server})
        self.queue = queue

    def send_topic(self, topic, message):
        """Send a message in a defined topic."""
        self.logger.info("Sending message through kafka topic: %s", topic)
        self.logger.debug('Topic: ' + topic + ' . Message: ' + message)
        self.producer.produce(topic, message, callback=self.delivery_callback)
        self.producer.flush()

    def delivery_callback(self, err, msg):
        """Indicate if the message have been received."""
        if err:
            self.logger.error('%% Message delivery failed: %s\n' % err)
            self.queue.put("error")
        else:
            self.logger.info('%% Message delivered to topic %s [partition %d]' %
                             (msg.topic(), msg.partition()))
            self.queue.put("success")
