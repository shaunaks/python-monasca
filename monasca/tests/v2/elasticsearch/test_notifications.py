# Copyright 2015 Carnegie Mellon University
#
# Author: Han Chen <hanc@andrew.cmu.edu>
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

import ast
import falcon
import mock
from oslo.config import fixture as fixture_config
from oslotest import base
import requests

from monasca.common import es_conn
from monasca.v2.elasticsearch import notifications

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
                    "_type":"notification_methods",
                    "_id":"c60ec47e-5038-4bf1-9f95-4046c6e9a719",
                    "_source":{
                        "type":"EMAIL",
                        "id":"c60ec47e-5038-4bf1-9f95-4046c6e9a719",
                        "name":"NotificationMethod",
                        "address":"hanc@andrew.cmu.edu"
                    },
                    "_index":"admin"
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
        "took":2
    }
"""


class TestParamUtil(base.BaseTestCase):

    def setUp(self):
        super(TestParamUtil, self).setUp()
        self.req = mock.Mock()


class Es_conn:
    def get_message_by_id(self, id):
        return response_str


class TestNotificationMethodDispatcher(base.BaseTestCase):

    def setUp(self):
        self.CONF = self.useFixture(fixture_config.Config()).conf
        self.CONF.notification.topic_notification_methods = 'fake'
        self.CONF.es_conn.uri = 'fake_es_uri'
        super(TestNotificationMethodDispatcher, self).setUp()
        res = mock.Mock()
        res.status_code = 200
        res.json.return_value = {
            "id": "35cc6f1c-3a29-49fb-a6fc-d9d97d190508",
            "links": [
                {
                    "rel": "self",
                    "href": "http://192.168.10.4:8080/v2.0/notification-"
                            "methods/35cc6f1c-3a29-49fb-a6fc-d9d97d190508"
                }
            ],
            "name": "Name of notification method",
            "type": "EMAIL",
            "address": "john.doe@hp.com"
        }
        with mock.patch.object(requests, 'get',
                               return_value=res):
            self.dispatcher_get = (
                notifications.NotificationMethodDispatcher({}))

        res.json.return_value = {}
        with mock.patch.object(requests, 'post',
                               return_value=res):
            self.dispatcher_post = (
                notifications.NotificationMethodDispatcher({}))

        with mock.patch.object(requests, 'put',
                               return_value=res):
            self.dispatcher_put = (
                notifications.NotificationMethodDispatcher({}))

        with mock.patch.object(requests, 'delete',
                               return_value=res):
            self.dispatcher_delete = (
                notifications.NotificationMethodDispatcher({}))

    def test_initialization(self):
        # test that the doc type of the es connection is fake
        self.assertEqual(self.dispatcher_get._es_conn.doc_type, 'fake')

        self.assertEqual(self.dispatcher_get._es_conn.uri, 'fake_es_uri/')

    def test_handle_notification_msg(self):
        with mock.patch.object(es_conn.ESConnection,
                               'post_messages',
                               return_value=200):
            msg = ast.literal_eval(
                '{"type":"EMAIL","request":"POST", '
                '"id":'
                '"c60ec47e-5038-4bf1-9f95-4046c6e9a719",'
                '"name":"NotificationMethod",'
                '"address":"hanc@andrew.cmu.edu"}')
            np = notifications.NotificationMethodDispatcher({})
            np.handle_notification_msg(msg)

        with mock.patch.object(es_conn.ESConnection, 'put_messages',
                               return_value=200):
            msg = ast.literal_eval(
                '{"type":"EMAIL","request":"PUT", '
                '"id":'
                '"c60ec47e-5038-4bf1-9f95-4046c6e9a719",'
                '"name":"NotificationMethod",'
                '"address":"hanc@andrew.cmu.edu"}')
            np = notifications.NotificationMethodDispatcher({})
            np.handle_notification_msg(msg)

        with mock.patch.object(es_conn.ESConnection, 'del_messages',
                               return_value=200):
            msg = ast.literal_eval(
                '{"type":"EMAIL","request":"DEL", '
                '"id":'
                '"c60ec47e-5038-4bf1-9f95-4046c6e9a719",'
                '"name":"NotificationMethod",'
                '"address":"hanc@andrew.cmu.edu"}')
            np = notifications.NotificationMethodDispatcher({})
            np.handle_notification_msg(msg)

    def test_do_get_notifications(self):
        res = mock.Mock()
        req = mock.Mock()

        req_result = mock.Mock()

        req_result.json.return_value = json.loads(response_str)
        req_result.status_code = 200

        with mock.patch.object(requests, 'get', return_value=req_result):
            (self.dispatcher_get.
                do_get_notification_methods(
                    req, res,
                    id="c60ec47e-5038-4bf1-9f95-4046c6e9a719"))

        # test that the response code is 200
        self.assertEqual(res.status, getattr(falcon, 'HTTP_200'))
        obj = json.loads(res.body)
        self.assertEqual(obj[0]['id'], 'c60ec47e-5038-4bf1-9f95-4046c6e9a719')
        self.assertEqual(obj[0]['type'], 'EMAIL')
        self.assertEqual(obj[0]['name'], 'NotificationMethod')
        self.assertEqual(obj[0]['address'], 'hanc@andrew.cmu.edu')
        self.assertEqual(len(obj), 1)

    def test_do_post_notifications(self):
        with mock.patch.object(notifications.NotificationMethodDispatcher,
                               'handle_notification_msg',
                               return_value=200):
            with mock.patch.object(ast, 'literal_eval',
                                   return_value=ast.literal_eval(
                                       "{'type': 'PAGEDUTY', "
                                       "'name': 'NotificationMethod2', "
                                       "'address': '1234567'}")):
                res = mock.Mock()
                (self.dispatcher_post.
                    do_post_notification_methods(mock.Mock(), res))

                self.assertEqual(getattr(falcon, 'HTTP_200'), res.status)

    def test_do_put_notifications(self):
        with mock.patch.object(notifications.NotificationMethodDispatcher,
                               'handle_notification_msg',
                               return_value=200):
            with mock.patch.object(ast, 'literal_eval',
                                   return_value=ast.literal_eval(
                                       "{'type': 'PAGEDUTY', "
                                       "'name': 'NotificationMethod2', "
                                       "'address': '1234567'}")):
                res = mock.Mock()
                (self.dispatcher_post.
                    do_put_notification_methods(
                        mock.Mock(), res,
                        id="c60ec47e-5038-4bf1-9f95-4046c6e9a719"))

                self.assertEqual(getattr(falcon, 'HTTP_200'), res.status)

    def test_do_delete_notifications(self):
        with mock.patch.object(notifications.NotificationMethodDispatcher,
                               'handle_notification_msg',
                               return_value=200):
            res = mock.Mock()
            (self.dispatcher_post.
                do_delete_notification_methods(
                    mock.Mock(), res,
                    id="c60ec47e-5038-4bf1-9f95-4046c6e9a719"))

            self.assertEqual(getattr(falcon, 'HTTP_200'), res.status)