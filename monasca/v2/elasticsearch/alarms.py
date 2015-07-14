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
from stevedore import driver

from monasca.common import es_conn
from monasca.common import namespace
from monasca.common import resource_api
from monasca.openstack.common import log


try:
    import ujson as json
except ImportError:
    import json

alarms_opts = [
    cfg.StrOpt('doc_type', default='alarms',
               help='The doc_type that alarm definitions will be saved to.'),
    cfg.StrOpt('index_strategy', default='timed',
               help='The index strategy used to create index name.'),
    cfg.StrOpt('index_prefix', default='data_',
               help='The index prefix where metrics were saved to.'),
    cfg.IntOpt('size', default=10000,
               help=('The query result limit. Any result set more than '
                     'the limit will be discarded.')),
]

cfg.CONF.register_opts(alarms_opts, group='alarms')

LOG = log.getLogger(__name__)


class AlarmDispatcher(object):

    def __init__(self, global_conf):
        LOG.debug('Initializing Alarm V2API!')
        super(AlarmDispatcher, self).__init__()
        self.doc_type = cfg.CONF.alarms.doc_type
        self.index_prefix = cfg.CONF.alarms.index_prefix
        self.size = cfg.CONF.alarms.size

        # load index strategy
        if cfg.CONF.alarms.index_strategy:
            self.index_strategy = driver.DriverManager(
                namespace.STRATEGY_NS,
                cfg.CONF.alarms.index_strategy,
                invoke_on_load=True,
                invoke_kwds={}).driver
            LOG.debug(self.index_strategy)
        else:
            self.index_strategy = None

        self._es_conn = es_conn.ESConnection(
            self.doc_type, self.index_strategy, self.index_prefix)

    def _get_alarms_response(self, res):
        if res and res.status_code == 200:
            obj = res.json()
            if obj:
                return obj.get('hits')
            return None
        else:
            return None

    def _get_alarms_helper(self, query_string):
        queries = []
        field_string = 'alarms.metrics.dimensions.'
        if query_string:
            params = query_string.split('&')
            for current_param in params:
                current_param_split = current_param.split('=')
                if current_param_split[0] == 'metric_dimensions':
                    current_dimension_split = (
                        current_param_split[1].split(','))
                    for current_dimension in current_dimension_split:
                        current_dimen_data = current_dimension.split(':')
                        queries.append({
                            'query_string': {
                                'default_field': (field_string +
                                                  current_dimen_data[0]),
                                'query': current_dimen_data[1]
                            }
                        })
                else:
                    queries.append({
                        'query_string': {
                            'default_field': current_param_split[0],
                            'query': current_param_split[1]
                        }
                    })
            LOG.debug(queries)
            query = {
                'query': {
                    'bool': {
                        'must': queries
                    }
                }
            }
        else:
            query = {}
        LOG.debug('Parsed Query: %s' % query)
        return query

    @resource_api.Restify('/v2.0/alarms', method='get')
    def do_get_alarms(self, req, res):
        LOG.debug('The alarms GET request is received!')

        # Extract the query string frm the request
        query_string = req.query_string
        LOG.debug('Request Query String: %s' % query_string)

        # Transform the query string with proper search format
        params = self._get_alarms_helper(query_string)
        LOG.debug('Query Data: %s' % params)

        es_res = self._es_conn.get_messages(params)
        res.status = getattr(falcon, 'HTTP_%s' % es_res.status_code)
        LOG.debug('Query to ElasticSearch returned Status: %s' %
                  es_res.status_code)

        es_res = self._get_alarms_response(es_res)
        LOG.debug('Query to ElasticSearch returned: %s' % es_res)

        res.body = ''
        try:
            if es_res["hits"]:
                res_data = es_res["hits"]
                res.body = '['
                for current_alarm in res_data:
                    if current_alarm:
                        res.body += json.dumps({
                            "id": current_alarm["_source"]["id"],
                            "links": [{"rel": "self",
                                       "href": req.uri}],
                            "alarm_definition": current_alarm["_source"]
                            ["alarm-definition"],
                            "metrics": current_alarm["_source"]["metrics"],
                            "state": current_alarm["_source"]["state"],
                            "sub_alarms": current_alarm["_source"]
                            ["sub_alarms"],
                            "state_updated_timestamp":
                                current_alarm["_source"]
                                ["state_updated_timestamp"],
                            "updated_timestamp": current_alarm["_source"]
                            ["updated_timestamp"],
                            "created_timestamp": current_alarm["_source"]
                            ["created_timestamp"]})
                        res.body += ','
                res.body = res.body[:-1]
                res.body += ']'
                res.content_type = 'application/json;charset=utf-8'
        except Exception:
            LOG.exception('Error occurred while handling Alarms Get Request.')

    @resource_api.Restify('/v2.0/alarms/{id}', method='get')
    def do_get_alarms_by_id(self, req, res, id):
        LOG.debug('The alarms by id GET request is received!')
        LOG.debug(id)

        es_res = self._es_conn.get_message_by_id(id)
        res.status = getattr(falcon, 'HTTP_%s' % es_res.status_code)
        LOG.debug('Query to ElasticSearch returned Status: %s' %
                  es_res.status_code)

        es_res = self._get_alarms_response(es_res)
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
                        "metrics": res_data["_source"]["metrics"],
                        "state": res_data["_source"]["state"],
                        "sub_alarms": res_data["_source"]["sub_alarms"],
                        "state_updated_timestamp":
                            res_data["_source"]["state_updated_timestamp"],
                        "updated_timestamp":
                            res_data["_source"]["updated_timestamp"],
                        "created_timestamp":
                            res_data["_source"]["created_timestamp"]}])

                    res.content_type = 'application/json;charset=utf-8'
            else:
                res.body = ''
        except Exception:
            LOG.exception('Error occurred while handling Alarm '
                          'Get By ID Request.')

    @resource_api.Restify('/v2.0/alarms/{id}', method='put')
    def do_put_alarms(self, req, res, id):
        LOG.debug("Put the alarm with id: %s" % id)
        try:
            msg = req.stream.read()
            put_msg = ast.literal_eval(msg)
            es_res = self._es_conn.put_messages(json.dumps(put_msg), id)
            LOG.debug('Query to ElasticSearch returned Status: %s' %
                      es_res)
            res.status = getattr(falcon, 'HTTP_%s' % es_res)
        except Exception:
            LOG.exception('Error occurred while handling Alarm Put Request.')

    @resource_api.Restify('/v2.0/alarms/{id}', method='delete')
    def do_delete_alarms(self, req, res, id):
        LOG.debug("Delete the alarm with id: %s" % id)
        try:
            es_res = self._es_conn.del_messages(id)
            LOG.debug('Query to ElasticSearch returned Status: %s' %
                      es_res)
            res.status = getattr(falcon, 'HTTP_%s' % es_res)
        except Exception:
            LOG.exception('Error occurred while handling '
                          'Alarm Delete Request.')
