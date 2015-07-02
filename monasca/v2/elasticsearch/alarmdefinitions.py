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


import ast
import falcon
from oslo.config import cfg
import uuid

from monasca.common import es_conn
from monasca.common import resource_api
from monasca.openstack.common import log


try:
    import ujson as json
except ImportError:
    import json


alarmdefinitions_opts = [
    cfg.StrOpt('topic', default='alarmdefinitions',
               help='The topic that alarm definitions will be published to.'),
    cfg.IntOpt('size', default=1000,
               help=('The query result limit. Any result set more than '
                     'the limit will be discarded.')),
]


alarmdefinitions_group = cfg.OptGroup(
    name='alarmdefinitions', title='alarmdefinitions')
cfg.CONF.register_group(alarmdefinitions_group)
cfg.CONF.register_opts(alarmdefinitions_opts, alarmdefinitions_group)

LOG = log.getLogger(__name__)


class AlarmDefinitionUtil(object):

    @staticmethod
    def severityparsing(msg):
        try:
            severity = msg["severity"]
            if (severity == 'LOW' or severity
                    == 'MEDIUM' or severity
                    == 'HIGH' or severity == 'CRITICAL'):
                return msg
            else:
                msg["severity"] = "LOW"
                return msg

        except Exception:
            return msg


class AlarmDefinitionDispatcher(object):

    def __init__(self, global_conf):
        LOG.debug('Initializing AlarmDefinition V2API!')
        super(AlarmDefinitionDispatcher, self).__init__()
        self.topic = cfg.CONF.alarmdefinitions.topic
        self.size = cfg.CONF.alarmdefinitions.size
        self._es_conn = es_conn.ESConnection(self.topic)

    def _get_alarm_definitions_response(self, res):
        if res and res.status_code == 200:
            obj = res.json()
            if obj:
                return obj.get('hits')
            return None
        else:
            return None

    @resource_api.Restify('/v2.0/alarm-definitions/', method='post')
    def do_post_alarm_definitions(self, req, res):
        LOG.debug('Creating the alarm definitions')
        msg = req.stream.read()
        LOG.debug("Message: %s" % msg)
        post_msg = ast.literal_eval(msg)

        # random uuid genearation for alarm definition
        id = str(uuid.uuid4())
        post_msg["id"] = id
        post_msg = AlarmDefinitionUtil.severityparsing(post_msg)
        LOG.debug("Post Alarm Definition method: %s" % post_msg)
        try:
            es_res = self._es_conn.post_messages(json.dumps(post_msg), id)
            LOG.debug('Query to ElasticSearch returned Status: %s' %
                      es_res)
            res.status = getattr(falcon, 'HTTP_%s' % es_res)
        except Exception:
            LOG.exception('Error occurred while handling '
                          'Alarm Definition Post Request.')

    @resource_api.Restify('/v2.0/alarm-definitions/{id}', method='get')
    def do_get_alarm_definitions(self, req, res, id):
        LOG.debug('The alarm definitions GET request is received!')
        LOG.debug(id)

        es_res = self._es_conn.get_message_by_id(id)
        res.status = getattr(falcon, 'HTTP_%s' % es_res.status_code)

        LOG.debug('Query to ElasticSearch returned Status: %s' %
                  es_res.status_code)
        es_res = self._get_alarm_definitions_response(es_res)
        LOG.debug('Query to ElasticSearch returned: %s' % es_res)

        res.body = ''
        try:
            if es_res["hits"]:
                res_data = es_res["hits"][0]
                if res_data:
                    res.body = json.dumps([{
                        "id": id,
                        "links": [{"rel": "self",
                                   "href": req.uri}],
                        "name": res_data["_source"]["name"],
                        "description":res_data["_source"]["description"],
                        "expression":res_data["_source"]["expression"],
                        "severity":res_data["_source"]["severity"],
                        "match_by":res_data["_source"]["match_by"],
                        "alarm_actions":res_data["_source"]["alarm_actions"],
                        "ok_actions":res_data["_source"]["ok_actions"],
                        "undetermined_actions":res_data["_source"]
                        ["undetermined_actions"]}])
                    res.content_type = 'application/json;charset=utf-8'
        except Exception:
            LOG.exception('Error occurred while handling Alarm Definition '
                          'Get Request.')

    @resource_api.Restify('/v2.0/alarm-definitions/{id}', method='put')
    def do_put_alarm_definitions(self, req, res, id):
        LOG.debug("Put the alarm definitions with id: %s" % id)
        try:
            msg = req.stream.read()
            put_msg = ast.literal_eval(msg)
            put_msg = AlarmDefinitionUtil.severityparsing(put_msg)
            es_res = self._es_conn.put_messages(json.dumps(put_msg), id)
            LOG.debug('Query to ElasticSearch returned Status: %s' %
                      es_res)
            res.status = getattr(falcon, 'HTTP_%s' % es_res)
        except Exception:
            LOG.exception('Error occurred while handling Alarm '
                          'Definition Put Request.')

    @resource_api.Restify('/v2.0/alarm-definitions/{id}', method='delete')
    def do_delete_alarm_definitions(self, req, res, id):
        LOG.debug("Delete the alarm definitions with id: %s" % id)
        try:
            es_res = self._es_conn.del_messages(id)
            LOG.debug('Query to ElasticSearch returned Status: %s' %
                      es_res)
            res.status = getattr(falcon, 'HTTP_%s' % es_res)
        except Exception:
            LOG.exception('Error occurred while handling Alarm '
                          'Definition Delete Request.')
