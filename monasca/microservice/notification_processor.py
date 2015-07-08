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
from monasca.common import email_sender
from monasca.openstack.common import log

LOG = log.getLogger(__name__)


class NotificationProcessor(object):
    def __init__(self):
        LOG.debug('initializing NotificationProcessor!')
        super(NotificationProcessor, self).__init__()
        self._email_sender = email_sender.EmailSender()
        self.email_addresses = []

    def _get_notification_method_response(self, res):
        if res and res.status_code == 200:
            obj = res.json()
            if obj:
                return obj.get('hits')
            return None
        else:
            return None

    def handle_alarm_msg(self, _es_conn, msg):
        if msg and msg.message:
            LOG.debug("Message received for alarm: " + msg.message.value)
            value = msg.message.value
            if value:
                # value's format is:
                # {
                #   "metrics": {
                #     "timestamp": 1432672915.409,
                #     "name": "biz",
                #     "value": 1500,
                #     "dimensions": {
                #       "key2": "value2",
                #       "key1": "value1"
                #     }
                #   },
                #   "state_updated_timestamp": 1432672915,
                #   "state": "ALARM",
                #   "alarm-definition": {
                #     "alarm_actions": [
                #       "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
                #     ],
                #     "undetermined_actions": [
                #       "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
                #     ],
                #     "name": "Average CPU percent greater than 10",
                #     "match_by": [
                #       "hostname"
                #     ],
                # "description": "The average CPU percent is greater than 10",
                #     "ok_actions": [
                #       "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
                #     ],
                # "expression": "max(foo{hostname=mini-mon,mu=na}, 120) > 1100
                #           and max(bar { asd = asd} )>1200 or avg(biz)>1300",
                #     "id": "c60ec47e-5038-4bf1-9f95-4046c6e91111",
                #     "severity": "LOW"
                #   }
                # }

                # convert to dict, and get state to determine
                # the actions(notification method id) needed.
                # the method id can be used to match the
                # notification method in elasticSearch
                # Then an email will be sent
                dict_msg = ast.literal_eval(value)
                state = dict_msg["state"]
                if state not in ["ALARM", "OK", "UNDETERMINED"]:
                    LOG.error("state of alarm is not defined as expected")
                    return

                actions = []
                if state == 'ALARM':
                    actions = dict_msg["alarm-definition"]["alarm_actions"]
                if state == 'OK':
                    actions = dict_msg["alarm-definition"]["ok_actions"]
                if state == 'UNDETERMINED':
                    actions = dict_msg[
                        "alarm-definition"]["undetermined_actions"]

                addresses = []
                types = []
                # the action_id is an id of notification method
                # there can be multiple ids in one alarm message with different
                # types
                for action_id in actions:

                    es_res = _es_conn.get_message_by_id(action_id)
                    es_res = self._get_notification_method_response(es_res)

                    LOG.debug('Query to ElasticSearch returned: %s' % es_res)

                    if es_res is None:
                        LOG.error("The provided is not defined as expected")
                        return

                    name = es_res["hits"][0]["_source"]["name"]
                    type = es_res["hits"][0]["_source"]["type"]
                    address = es_res["hits"][0]["_source"]["address"]

                    types.append(type)
                    addresses.append(address)

                for i in range(len(types)):
                    if types[i] == "EMAIL":
                        self.email_addresses.append(addresses[i])

                self._email_sender.send_emails(
                    self.email_addresses,
                    "Alarm from Monasca:" + name + "-" +
                    dict_msg["alarm-definition"]["description"],
                    str(dict_msg))