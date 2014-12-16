# Copyright 2014 Hewlett-Packard
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

import falcon
import mock
from oslo.config import fixture as fixture_config
from oslotest import base

from monasca.common import kafka_conn
from monasca.v2.elasticsearch import metrics


class TestMetricDispatcher(base.BaseTestCase):

    def setUp(self):
        self.CONF = self.useFixture(fixture_config.Config()).conf
        self.CONF.kafka_opts.uri = 'fake_url'
        self.CONF.metrics.topic = 'fake'
        self.CONF.es.uri = 'fake_es_uri'
        super(TestMetricDispatcher, self).setUp()
        self.dispatcher = metrics.MetricDispatcher({})

    def test_connections(self):
        # test that the kafka connection uri should be 'fake' as it was passed
        # in from configuration
        self.assertEqual(self.dispatcher._kafka_conn.uri, 'fake_url')

        # test that the topic is metrics as it was passed into dispatcher
        self.assertEqual(self.dispatcher._kafka_conn.topic, 'fake')

        # test that the doc type of the es connection is fake
        self.assertEqual(self.dispatcher._es_conn.doc_type, 'fake')

        self.assertEqual(self.dispatcher._es_conn.uri, 'fake_es_uri/')

    def test_post_data(self):
        with mock.patch.object(kafka_conn.KafkaConnection, 'send_messages',
                               return_value=204):
            res = mock.Mock()
            self.dispatcher.post_data(mock.Mock(), res)

        # test that the response code is 204
        self.assertEqual(getattr(falcon, 'HTTP_204'), res.status)

        with mock.patch.object(kafka_conn.KafkaConnection, 'send_messages',
                               return_value=400):
            res = mock.Mock()
            self.dispatcher.post_data(mock.Mock(), res)

        # test that the response code is 204
        self.assertEqual(getattr(falcon, 'HTTP_400'), res.status)

    def test_do_get_metrics(self):
        res = mock.Mock()
        self.dispatcher.do_get_metrics(mock.Mock(), res)

        # test that the response code is 501
        self.assertEqual(getattr(falcon, 'HTTP_501'), res.status)

    def test_do_post_metrics(self):
        with mock.patch.object(kafka_conn.KafkaConnection, 'send_messages',
                               return_value=204):
            res = mock.Mock()
            self.dispatcher.do_post_metrics(mock.Mock(), res)

        self.assertEqual(getattr(falcon, 'HTTP_204'), res.status)