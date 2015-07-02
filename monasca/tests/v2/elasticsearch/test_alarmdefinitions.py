# Copyright 2015 Carnegie Mellon University
#
# Author: Shaunak Shatmanyu <shatmanyu@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
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
import requests

from monasca.common import es_conn
from monasca.v2.elasticsearch import alarmdefinitions

try:
    import ujson as json
except ImportError:
    import json


response_str = """
            {
                "hits":{
                    "hits":[
                        {
                            "_score":1.0,
                            "_type":"alarmdefinitions",
                            "_id":"72df5ccb-ec6a-4bb4-a15c-939467ccdde0",
                            "_source":{
                                "id":"72df5ccb-ec6a-4bb4-a15c-939467ccdde0",
                                "name":"CPU usage test",
                                "alarm_actions":
                                "c60ec47e-5038-4bf1-9f95-4046c6e9a719",
                                "undetermined_actions":
                                "c60ec47e-5038-4bf1-9t95-4046c6e9a759",
                                "ok_actions":
                                "c60ec47e-5038-4bf1-9f95-4046cte9a759",
                                "match_by":"hostname",
                                "severity":"LOW",
                                "expression":
                                "max(cpu.usage{os=linux},600)>15",
                                "description": "Max CPU 15"
                            },
                            "_index":"data_20150601000000"
                        }
                    ],
                    "total":1,
                    "max_score":1.0
                },
                "_shards":{
                    "successful":5,
                    "failed":0,
                    "total":5
                },
                "took":2,
            }
        """


class TestAlarmDefinitionUtil(base.BaseTestCase):

    def setUp(self):
        super(TestAlarmDefinitionUtil, self).setUp()
        self.req = mock.Mock()


class TestAlarmDefinitionDispatcher(base.BaseTestCase):

    def setUp(self):
        self.CONF = self.useFixture(fixture_config.Config()).conf
        self.CONF.alarmdefinitions.topic = 'fake'
        self.CONF.es.uri = 'fake_es_uri'
        super(TestAlarmDefinitionDispatcher, self).setUp()
        res = mock.Mock()
        res.status_code = 200
        res.json.return_value = {
            "id": "72df5ccb-ec6a-4bb4-a15c-939467ccdde0",
            "links": [
                {
                    "rel": "self",
                    "href": "http://127.0.0.1:9090/v2.0/alarm-definitions/"
                            "72df5ccb-ec6a-4bb4-a15c-939467ccdde0"
                }
            ],
            "name": "CPU usage test",
            "alarm_actions": "c60ec47e-5038-4bf1-9f95-4046c6e9a719",
            "undetermined_actions": "c60ec47e-5038-4bf1-9t95-4046c6e9a759",
            "ok_actions": "c60ec47e-5038-4bf1-9f95-4046cte9a759",
            "match_by": "hostname",
            "severity": "LOW",
            "expression": "max(cpu.usage{os=linux},600)>15",
            "description": "Max CPU 15"
        }
        with mock.patch.object(requests, 'get',
                               return_value=res):
            self.dispatcher_get = (
                alarmdefinitions.AlarmDefinitionDispatcher({}))

        res.json.return_value = {}

        self.dispatcher_post = (
            alarmdefinitions.AlarmDefinitionDispatcher({}))

        self.dispatcher_put = (
            alarmdefinitions.AlarmDefinitionDispatcher({}))

        self.dispatcher_delete = (
            alarmdefinitions.AlarmDefinitionDispatcher({}))

    def test_initialization(self):
        # test that the doc type of the es connection is fake
        self.assertEqual(self.dispatcher_get._es_conn.doc_type, 'fake')

        self.assertEqual(self.dispatcher_get._es_conn.uri, 'fake_es_uri/')

    def test_do_get_alarm_definitions(self):
        res = mock.Mock()
        req = mock.Mock()

        req_result = mock.Mock()

        req_result.json.return_value = json.loads(response_str)
        req_result.status_code = 200

        with mock.patch.object(requests, 'get', return_value=req_result):
            self.dispatcher_get.do_get_alarm_definitions(
                req, res, id="72df5ccb-ec6a-4bb4-a15c-939467ccdde0")

        # test that the response code is 200
        self.assertEqual(res.status, getattr(falcon, 'HTTP_200'))
        obj = json.loads(res.body)
        self.assertEqual(obj[0]['id'],
                         "72df5ccb-ec6a-4bb4-a15c-939467ccdde0")
        self.assertEqual(obj[0]['name'], "CPU usage test")
        self.assertEqual(obj[0]['alarm_actions'],
                         "c60ec47e-5038-4bf1-9f95-4046c6e9a719")
        self.assertEqual(obj[0]['undetermined_actions'],
                         "c60ec47e-5038-4bf1-9t95-4046c6e9a759")
        self.assertEqual(obj[0]['ok_actions'],
                         "c60ec47e-5038-4bf1-9f95-4046cte9a759")
        self.assertEqual(obj[0]['match_by'], "hostname")
        self.assertEqual(obj[0]['severity'], "LOW")
        self.assertEqual(obj[0]['expression'],
                         "max(cpu.usage{os=linux},600)>15")
        self.assertEqual(obj[0]['description'], "Max CPU 15")
        self.assertEqual(len(obj), 1)

    def test_do_post_alarm_definitions(self):
        req = mock.Mock()
        res = mock.Mock()
        req_result = mock.Mock()
        req_result.status_code = 201

        with mock.patch.object(requests, 'post', return_value=req_result):
            with mock.patch.object(req.stream, 'read',
                                   return_value="{ 'name': 'CPU usage test', "
                                                "'alarm_actions': "
                                                "'c60ec47e-5038-4bf1-9f95-"
                                                "4046c6e9a719', "
                                                "'undetermined_actions': "
                                                "'c60ec47e-5038-4bf1-9t95-"
                                                "4046c6e9a759', 'ok_actions':"
                                                " 'c60ec47e-5038-4bf1-9f95-"
                                                "4046cte9a759', "
                                                "'match_by': 'hostname', "
                                                "'severity': 'LOW', "
                                                "'expression': "
                                                "'max(cpu.usage{os=linux},"
                                                "600)"
                                                ">15', 'description': "
                                                "'Max CPU 15'"
                                                "}"
                                   ):
                self.dispatcher_post.do_post_alarm_definitions(
                    req, res)
                self.assertEqual(res.status, getattr(falcon, 'HTTP_201'))

    def test_do_put_alarm_definitions(self):
        req = mock.Mock()
        res = mock.Mock()
        req_result = mock.Mock()
        req_result.status_code = 200

        with mock.patch.object(requests, 'put', return_value=req_result):
            with mock.patch.object(req.stream, 'read',
                                   return_value="{ 'name': 'CPU usage test', "
                                                "'alarm_actions': "
                                                "'c60ec47e-5038-4bf1-9f95-"
                                                "4046c6e9a719', "
                                                "'undetermined_actions': "
                                                "'c60ec47e-5038-4bf1-9t95-"
                                                "4046c6e9a759', 'ok_actions':"
                                                " 'c60ec47e-5038-4bf1-9f95-"
                                                "4046cte9a759', "
                                                "'match_by': 'hostname', "
                                                "'severity': 'LOW', "
                                                "'expression': "
                                                "'max(cpu.usage{os=linux},"
                                                "600)"
                                                ">15', 'description': "
                                                "'Max CPU 15'"
                                                "}"
                                   ):
                self.dispatcher_put.do_put_alarm_definitions(
                    req, res, id="72df5ccb-ec6a-4bb4-a15c-939467ccdde0")
                self.assertEqual(res.status, getattr(falcon, 'HTTP_200'))

    def test_do_delete_alarm_definitions(self):
        with mock.patch.object(es_conn.ESConnection, 'del_messages',
                               return_value=200):
            res = mock.Mock()
            self.dispatcher_delete.do_delete_alarm_definitions(
                mock.Mock(), res, id="72df5ccb-ec6a-4bb4-a15c-939467ccdde0")
            self.assertEqual(res.status, getattr(falcon, 'HTTP_200'))
