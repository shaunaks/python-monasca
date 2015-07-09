# Copyright 2015 Carnegie Mellon University
#
# Author: Han Chen <hanc@andrew.cmu.edu>
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
import mock
from monasca.common import kafka_conn
from monasca.microservice import threshold_engine as engine
from oslo.config import fixture as fixture_config
from oslotest import base
from stevedore import driver


class TestThresholdEngine(base.BaseTestCase):
    def setUp(self):
        self.CONF = self.useFixture(fixture_config.Config()).conf
        self.CONF.kafka_opts.uri = 'fake_url'
        self.CONF.thresholdengine.metrics_topic = 'fake_metrics'
        self.CONF.thresholdengine.definition_topic = (
            'fake_alarmdefinitions')
        self.CONF.thresholdengine.alarm_topic = 'fake_alarms'
        self.CONF.thresholdengine.check_alarm_interval = 10
        super(TestThresholdEngine, self).setUp()
        self.thresh_engine = engine.ThresholdEngine()

    def test_initialization(self):
        # Test Kafka connection uri and topic
        self.assertEqual(self.thresh_engine.thread_metrics.
                         _consume_kafka_conn.uri, 'fake_url')
        self.assertEqual(self.thresh_engine.thread_metrics.
                         _consume_kafka_conn.topic, 'fake_metrics')
        self.assertEqual(self.thresh_engine.thread_alarm_def.
                         _consume_kafka_conn.uri, 'fake_url')
        self.assertEqual(self.thresh_engine.thread_alarm_def.
                         _consume_kafka_conn.topic, 'fake_alarmdefinitions')
        self.assertEqual(self.thresh_engine.thread_alarm.
                         _publish_kafka_conn.uri, 'fake_url')
        self.assertEqual(self.thresh_engine.thread_alarm.
                         _publish_kafka_conn.topic, 'fake_alarms')
        self.assertEqual(self.thresh_engine.thread_alarm.interval, 10)

    def test_consume_alarm_def(self):
        # test create new alarm definition
        ad = [{'id': 'fake_id_1', 'request': 'POST'},
              {'id': 'fake_id_2', 'request': 'POST'},
              {'id': 'fake_id_2', 'request': 'POST'}]
        alarm_def = [mock.Mock(), mock.Mock(), mock.Mock()]
        for i in range(len(ad)):
            alarm_def[i].message.value = json.dumps(ad[i])
        processor = mock.Mock()
        with mock.patch.object(driver.DriverManager, '__init__',
                               return_value=None):
            with mock.patch.object(driver.DriverManager, 'driver',
                                   return_value=processor):
                with mock.patch.object(kafka_conn.KafkaConnection,
                                       'get_messages',
                                       return_value=alarm_def):
                    self.thresh_engine.thread_alarm_def.read_alarm_def()
        print (self.thresh_engine.thread_alarm_def.thresholding_processors)
        tp = self.thresh_engine.thread_alarm_def.thresholding_processors
        self.assertEqual(2, len(tp))
        self.assertIn('fake_id_1', tp)
        self.assertIn('fake_id_2', tp)
        self.assertNotIn('fake_id_3', tp)

        # test update alarm definition
        ad = [{'id': 'fake_id_1', 'request': 'PUT'},
              {'id': 'fake_id_2', 'request': 'PUT'},
              {'id': 'fake_id_3', 'request': 'PUT'}]
        alarm_def = [mock.Mock(), mock.Mock(), mock.Mock()]
        for i in range(len(ad)):
            alarm_def[i].message.value = json.dumps(ad[i])
        with mock.patch.object(kafka_conn.KafkaConnection, 'get_messages',
                               return_value=alarm_def):
            self.thresh_engine.thread_alarm_def.read_alarm_def()
        print (self.thresh_engine.thread_alarm_def.thresholding_processors)
        tp = self.thresh_engine.thread_alarm_def.thresholding_processors
        self.assertEqual(2, len(tp))
        self.assertIn('fake_id_1', tp)
        self.assertIn('fake_id_2', tp)
        self.assertNotIn('fake_id_3', tp)

        # test delete alarm definition
        ad = [{'id': 'fake_id_1', 'request': 'DEL'},
              {'id': 'fake_id_3', 'request': 'DEL'}]
        alarm_def = [mock.Mock(), mock.Mock()]
        for i in range(len(ad)):
            alarm_def[i].message.value = json.dumps(ad[i])
        with mock.patch.object(kafka_conn.KafkaConnection, 'get_messages',
                               return_value=alarm_def):
            self.thresh_engine.thread_alarm_def.read_alarm_def()
        print (self.thresh_engine.thread_alarm_def.thresholding_processors)
        tp = self.thresh_engine.thread_alarm_def.thresholding_processors
        self.assertEqual(1, len(tp))
        self.assertNotIn('fake_id_1', tp)
        self.assertIn('fake_id_2', tp)
        self.assertNotIn('fake_id_3', tp)

    def test_consume_metrics(self):
        # test consume received metrics
        raw_metrics = [
            '{"timestamp": "2015-06-25T14:01:36Z", "name": "biz1", '
            '"value": 1300, '
            '"dimensions": {"key2": "value2", "hostname": "h1"}}',
            '{"timestamp": "2015-06-25T14:01:36Z", "name": "biz2", '
            '"value": 1500, '
            '"dimensions": {"key2": "value2", "hostname": "h2"}}',
            '{"timestamp": "2015-06-25T14:01:36Z", "name": "biz3", '
            '"value": 1200, '
            '"dimensions": {"key2": "value2", "hostname": "h3"}}']
        metrics = [mock.Mock(), mock.Mock(), mock.Mock()]
        for i in range(len(raw_metrics)):
            metrics[i].message.value = raw_metrics[i]
        pre = self.thresh_engine.thread_metrics.thresholding_processors.copy()
        with mock.patch.object(kafka_conn.KafkaConnection, 'get_messages',
                               return_value=metrics):
            self.thresh_engine.thread_metrics.read_metrics()
        self.assertEqual(pre,
                         self.thresh_engine.thread_metrics.
                         thresholding_processors)

        # read one alarm definition and test consume metrics again
        processor = mock.Mock()
        alarm_def = [mock.Mock()]
        alarm_def[0].message.value = json.dumps(
            {'id': 'fake_id_1', 'request': 'POST'})
        with mock.patch.object(driver.DriverManager, '__init__',
                               return_value=None):
            with mock.patch.object(driver.DriverManager, 'driver',
                                   return_value=processor):
                with mock.patch.object(kafka_conn.KafkaConnection,
                                       'get_messages',
                                       return_value=alarm_def):
                    self.thresh_engine.thread_alarm_def.read_alarm_def()
        pre = self.thresh_engine.thread_metrics.thresholding_processors.copy()
        with mock.patch.object(kafka_conn.KafkaConnection, 'get_messages',
                               return_value=metrics):
            self.thresh_engine.thread_metrics.read_metrics()
        self.assertEqual(pre,
                         self.thresh_engine.thread_metrics.
                         thresholding_processors)
        print (self.thresh_engine.thread_metrics.thresholding_processors)

    def test_publish_alarms(self):
        # read one alarm definition
        processor = mock.Mock()
        alarm_def = [mock.Mock()]
        alarm_def[0].message.value = json.dumps(
            {'id': 'fake_id_1', 'request': 'POST'})
        with mock.patch.object(driver.DriverManager, '__init__',
                               return_value=None):
            with mock.patch.object(driver.DriverManager, 'driver',
                                   return_value=processor):
                with mock.patch.object(kafka_conn.KafkaConnection,
                                       'get_messages',
                                       return_value=alarm_def):
                    self.thresh_engine.thread_alarm_def.read_alarm_def()

        # test send alarms
        pre = self.thresh_engine.thread_alarm.thresholding_processors.copy()
        with mock.patch.object(kafka_conn.KafkaConnection, 'send_messages',
                               return_value=None):
            self.thresh_engine.thread_alarm.send_alarm()
        self.assertEqual(pre,
                         self.thresh_engine.thread_alarm.
                         thresholding_processors)
