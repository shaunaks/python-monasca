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

import copy
import falcon
import mock
from oslo.config import fixture as fixture_config
from oslotest import base
import requests

from monasca.common import kafka_conn
from monasca.v2.elasticsearch import metrics

try:
    import ujson as json
except ImportError:
    import json


class TestMetricDispatcher(base.BaseTestCase):

    def setUp(self):
        self.CONF = self.useFixture(fixture_config.Config()).conf
        self.CONF.kafka_opts.uri = 'fake_url'
        self.CONF.metrics.topic = 'fake'
        self.CONF.es.uri = 'fake_es_uri'
        super(TestMetricDispatcher, self).setUp()
        res = mock.Mock()
        res.status_code = 200
        res.json.return_value = {"data": {"mappings": {"fake": {
            "properties": {
                "dimensions": {"properties": {
                    "key1": {"type": "long"}, "key2": {"type": "long"},
                    "rkey0": {"type": "long"}, "rkey1": {"type": "long"},
                    "rkey2": {"type": "long"}, "rkey3": {"type": "long"}}},
                "name": {"type": "string", "index": "not_analyzed"},
                "timestamp": {"type": "string", "index": "not_analyzed"},
                "value": {"type": "double"}}}}}}
        with mock.patch.object(requests, 'get',
                               return_value=res):
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

        # test that the query url is correctly formed
        self.assertEqual(self.dispatcher._query_url,
                         'fake_es_uri/monasca_*/fake/_search')

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

    def test__handle_req_name(self):
        req = mock.Mock()

        def _side_effect(arg):
            if arg == 'name':
                return 'tongli'
            elif arg == 'dimensions':
                return 'key1:100, key2:200'
        req.get_param.side_effect = _side_effect

        body = copy.deepcopy(self.dispatcher._query_body)
        self.dispatcher._handle_req_name(req, body)

        self.assertEqual(body['query']['filtered']['filter']['bool']['must'],
                         [{'term': {'name': 'tongli'}}])

    def test__handle_req_dimensions(self):
        req = mock.Mock()

        def _side_effect(arg):
            if arg == 'name':
                return 'tongli'
            elif arg == 'dimensions':
                return 'key1:100, key2:200, key3:, key4, key24:12:29,'
        req.get_param.side_effect = _side_effect

        body = copy.deepcopy(self.dispatcher._query_body)
        self.dispatcher._handle_req_dimensions(req, body)

        # notice that the query parameter for dimension contains 3 invalid
        # ones, these should be ignored.
        self.assertEqual(body['query']['filtered']['filter']['bool']['must'],
                         [{'term': {'dimensions.key1': '100'}},
                          {'term': {'dimensions.key2': '200'}}])

    def test_do_get_metrics(self):
        res = mock.Mock()
        req = mock.Mock()

        def _side_effect(arg):
            if arg == 'name':
                return 'tongli'
            elif arg == 'dimensions':
                return 'key1:100, key2:200'
        req.get_param.side_effect = _side_effect

        req_result = mock.Mock()
        req_result.json.return_value = {"aggregations": {
            "name": {"doc_count_error_upper_bound": 10,
                     "sum_other_doc_count": 903,
                     "buckets": [{"key": "BJAMCA", "doc_count": 10,
                                  "key1": {"doc_count_error_upper_bound": 0,
                                           "sum_other_doc_count": 0,
                                           "buckets": []}}]}}}

        req_result.status_code = 200

        with mock.patch.object(requests, 'post', return_value=req_result):
            self.dispatcher.do_get_metrics(req, res)

        # test that the response code is 200
        self.assertEqual(res.status, getattr(falcon, 'HTTP_200'))
        obj = json.loads(res.stream)
        self.assertEqual(obj[0]['name'], 'BJAMCA')
        self.assertEqual(obj[0]['dimensions'], {})

    def test_do_post_metrics(self):
        with mock.patch.object(kafka_conn.KafkaConnection, 'send_messages',
                               return_value=204):
            res = mock.Mock()
            self.dispatcher.do_post_metrics(mock.Mock(), res)

        self.assertEqual(getattr(falcon, 'HTTP_204'), res.status)