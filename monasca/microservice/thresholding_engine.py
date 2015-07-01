# Copyright 2015 Carnegie Mellon University
#
# Author: Yihan Wang <wangff9@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import json
from monasca.common import kafka_conn
from monasca.openstack.common import log
from monasca.openstack.common import service as os_service
from oslo.config import cfg
from stevedore import driver
import threading
import time

PROCESSOR_NAMESPACE = 'monasca.message.processor'
lock = threading.RLock()

th_opts = [
    cfg.StrOpt('metrics_topic',
               default='metrics',
               help='topics to read metrics'),
    cfg.StrOpt('definition_topic',
               default='alarmdefinitions',
               help='topic to read alarm definitions'),
    cfg.StrOpt('alarm_topic',
               default='alarm',
               help='topic to send alarms'),
    cfg.StrOpt('processor',
               default='thresholding_processor',
               help='the thresh processor'),
    cfg.IntOpt('check_alarm_interval',
               default=60)
]

th_group = cfg.OptGroup(name='thresholding_engine',
                        title='thresholding_engine')
cfg.CONF.register_group(th_group)
cfg.CONF.register_opts(th_opts, th_group)

LOG = log.getLogger(__name__)


class AlarmPublisher(threading.Thread):
    """The thread to publish alarm messages."""
    def __init__(self, t_name, tp):
        threading.Thread.__init__(self, name=t_name)
        self._publish_kafka_conn = None
        topic = cfg.CONF.thresholding_engine.alarm_topic
        self._publish_kafka_conn = (
            kafka_conn.KafkaConnection(topic))
        self.interval = cfg.CONF.thresholding_engine.check_alarm_interval
        self.thresholding_processors = tp

    def send_alarm(self):
        if self._publish_kafka_conn:
            if lock.acquire():
                for processor in self.thresholding_processors:
                    for alarm in (self.thresholding_processors
                                  [processor].process_alarms()):
                        LOG.debug(alarm)
                        self._publish_kafka_conn.send_messages(alarm)
            lock.release()

    def run(self):
        while True:
            try:
                self.send_alarm()
                time.sleep(self.interval)
            except Exception:
                LOG.exception(
                    'Error occurred while publishing alarm messages.')

    def stop(self):
        self._publish_kafka_conn.close()


class MetricsConsumer(threading.Thread):
    """The thread to read metrics."""
    def __init__(self, t_name, tp):
        threading.Thread.__init__(self, name=t_name)
        self._consume_kafka_conn = None
        topic = cfg.CONF.thresholding_engine.metrics_topic
        self._consume_kafka_conn = kafka_conn.KafkaConnection(topic)
        self.thresholding_processors = tp

    def read_metrics(self):
        def consume_metrics():
            if lock.acquire():
                for alarm_def in self.thresholding_processors:
                    processor = self.thresholding_processors[alarm_def]
                    processor.process_metrics(msg.message.value)
            lock.release()

        if self._consume_kafka_conn:
            for msg in self._consume_kafka_conn.get_messages():
                if msg and msg.message:
                    LOG.debug(msg.message.value)
                    consume_metrics()
            self._consume_kafka_conn.commit()

    def run(self):
        while True:
            try:
                self.read_metrics()
            except Exception:
                LOG.exception('Error occurred while reading metrics messages.')

    def stop(self):
        self._consume_kafka_conn.close()


class AlarmDefinitionConsumer(threading.Thread):
    """The thread to process alarm definitions."""
    def __init__(self, t_name, tp):
        threading.Thread.__init__(self, name=t_name)
        self._consume_kafka_conn = None
        topic = cfg.CONF.thresholding_engine.definition_topic
        self._consume_kafka_conn = (
            kafka_conn.KafkaConnection(topic))
        self.thresholding_processors = tp

    def read_alarm_def(self):
        def create_alarm_processor():
            if temp_alarm_def['id'] in self.thresholding_processors:
                LOG.debug('already exsist alarm definition')
                return
            if lock.acquire():
                self.thresholding_processors[temp_alarm_def['id']] = (
                    driver.DriverManager(
                        PROCESSOR_NAMESPACE,
                        cfg.CONF.thresholding_engine.processor,
                        invoke_on_load=True,
                        invoke_args=(msg.message.value,)).driver)
            lock.release()

        def update_alarm_processor():
            if lock.acquire():
                updated = False
                if temp_alarm_def['id'] in self.thresholding_processors:
                    updated = (self.thresholding_processors
                               [temp_alarm_def['id']]
                               .update_thresh_processor(msg.message.value))
                if updated:
                    LOG.debug('alarm definition updates successfully!')
                else:
                    LOG.debug('alarm definition update fail!')
            lock.release()

        def delete_alarm_processor():
            if lock.acquire():
                if temp_alarm_def['id'] in self.thresholding_processors:
                    self.thresholding_processors.pop(temp_alarm_def['id'])
            lock.release()

        if self._consume_kafka_conn:
            for msg in self._consume_kafka_conn.get_messages():
                if msg and msg.message:
                    LOG.debug(msg.message.value)
                    temp_alarm_def = json.loads(msg.message.value)
                    if temp_alarm_def['request'] == 'POST':
                        create_alarm_processor()
                    elif temp_alarm_def['request'] == 'PUT':
                        update_alarm_processor()
                    elif temp_alarm_def['request'] == 'DEL':
                        delete_alarm_processor()
            self._consume_kafka_conn.commit()

    def run(self):
        while True:
            try:
                self.read_alarm_def()
            except Exception:
                LOG.exception('Error occurred '
                              'while reading alarm def messages.')

    def stop(self):
        self._consume_kafka_conn.close()


class ThresholdingEngine(os_service.Service):
    def __init__(self, threads=1000):
        super(ThresholdingEngine, self).__init__(threads)
        self.thresholding_processors = {}
        self.thread_send = None
        self.thread_read = None
        try:
            self.thread_alarm = AlarmPublisher(
                'alarm_publisher',
                self.thresholding_processors)
        except Exception:
            self.thread_alarm = None
        try:
            self.thread_alarm_def = AlarmDefinitionConsumer(
                'alarm_def_consumer',
                self.thresholding_processors)
        except Exception:
            self.thread_alarm_def = None
        try:
            self.thread_metrics = MetricsConsumer(
                'metrics_consumer',
                self.thresholding_processors)
        except Exception:
            self.thread_metrics = None

    def start(self):
        try:
            self.thread_alarm.start()
            self.thread_alarm_def.start()
            self.thread_metrics.start()
            LOG.info('Starting thresh processing succeed!')
        except Exception:
            LOG.debug('Starting thresh processing failed!')

    def stop(self):
        try:
            if self.thread_alarm:
                self.thread_alarm.stop()
            if self.thread_alarm_def:
                self.thread_alarm_def.stop()
            if self.thread_metrics:
                self.thread_metrics.stop()
        except Exception:
            LOG.debug('Terminate thresh process threads error')
        super(ThresholdingEngine, self).stop()
