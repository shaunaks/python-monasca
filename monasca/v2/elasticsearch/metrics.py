# Copyright 2013 IBM Corp
#
# Author: Tong Li <litong01@us.ibm.com>
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

import copy
import falcon
from oslo.config import cfg
import requests

from monasca.common import es_conn
from monasca.common import kafka_conn
from monasca.common import resource_api
from monasca.openstack.common import log

try:
    import ujson as json
except ImportError:
    import json


metrics_opts = [
    cfg.StrOpt('topic', default='metrics',
               help='The topic that metrics will be published to.'),
    cfg.IntOpt('size', default=10000,
               help=('The query result limit. Any result set more than '
                     'the limit will be discarded. To see all the matching '
                     'result, narrow your search by using a small time '
                     'window or strong matching name')),
]

metrics_group = cfg.OptGroup(name='metrics', title='metrics')
cfg.CONF.register_group(metrics_group)
cfg.CONF.register_opts(metrics_opts, metrics_group)

LOG = log.getLogger(__name__)


class MetricDispatcher(object):
    def __init__(self, global_conf):
        LOG.debug('initializing V2API!')
        super(MetricDispatcher, self).__init__()
        self.topic = cfg.CONF.metrics.topic
        self.size = cfg.CONF.metrics.size
        self._kafka_conn = kafka_conn.KafkaConnection(self.topic)
        self._es_conn = es_conn.ESConnection(self.topic)

        # Setup the get metrics query body pattern
        self._query_body = {
            "query": {"filtered": {"filter": {"bool": {"must": []}}}},
            "size": self.size}

        self._aggs_body = {}
        self._sort_clause = []

        # Setup the get metrics query url, the url should be similar to this:
        # http://host:port/data_20141201/metrics/_search
        # the url should be made of es_conn uri, the index prefix, metrics
        # dispatcher topic, then add the key word _search.
        self._query_url = ''.join([self._es_conn.uri,
                                  self._es_conn.index_prefix, '*/',
                                  cfg.CONF.metrics.topic,
                                  '/_search'])

        # the url to get all the properties of metrics
        self._query_mapping_url = ''.join([self._es_conn.uri,
                                           self._es_conn.index_prefix,
                                           '*/_mappings/',
                                           cfg.CONF.metrics.topic])

        self._dim_props = {}
        self._get_dimension_keys()
        self._make_agg_clause()

    def _get_dimension_keys(self):
        res = requests.get(self._query_mapping_url)
        if res.status_code == 200:
            for key in res.json():
                mappings = res.json()[key]['mappings']
                break
            if mappings:
                properties = mappings[cfg.CONF.metrics.topic]['properties']
                if properties['dimensions']:
                    self._dim_props = properties['dimensions']['properties']

    def _make_agg_clause(self):
        if self._dim_props:
            self._aggs_body = {
                'name': {'terms': {'field': 'name'},
                         'aggs': {}}}

            self._sort_clause = [{'name': {'order': 'asc'}}]

            aggs = self._aggs_body['name']['aggs']
            for prop in self._dim_props:
                aggs[prop] = {'terms': {'field': 'dimensions.' + prop,
                                        'size': 0}}
                aggs[prop]['aggs'] = {}
                aggs = aggs[prop]['aggs']
                self._sort_clause.append(
                    {'dimensions.' + prop: {'order': 'asc'}})

    def post_data(self, req, res):
        LOG.debug('Getting the call.')
        msg = req.stream.read()

        code = self._kafka_conn.send_messages(msg)
        res.status = getattr(falcon, 'HTTP_' + str(code))

    def _handle_req_name(self, req, body):
        name = req.get_param('name')
        if name:
            body['query']['filtered']['filter']['bool']['must'].append(
                {'prefix': {'name': name.strip()}})

    def _handle_req_start_time(self, req, body):
        start_time = req.get_param('start_time')
        if start_time:
            body['query']['filtered']['filter']['bool']['must'].append(
                {'range': {'timestamp': {'gte': start_time.strip()}}})

    def _handle_req_dimensions(self, req, body):
        dimensions = req.get_param('dimensions')
        if dimensions:
            terms = []

            def _handle_pair(pair):
                param = pair.split(':')
                if len(param) == 2 and param[0] and param[1]:
                    key = param[0].strip()
                    value = param[1].strip()
                    try:
                        value = float(param[1].strip)
                    except Exception:
                        pass
                    terms.append({'term': {'dimensions.' + key: value}})
            map(_handle_pair, dimensions.split(','))
            body['query']['filtered']['filter']['bool']['must'] += terms

    @resource_api.Restify('/v2.0/metrics/', method='get')
    def do_get_metrics(self, req, res):
        LOG.debug('The metrics GET request is received!')
        body = copy.deepcopy(self._query_body)
        self._handle_req_name(req, body)
        self._handle_req_dimensions(req, body)
        self._handle_req_start_time(req, body)

        # if there is no name or dimension, we do not need filter clause
        if not body['query']['filtered']['filter']['bool']['must']:
            del body['query']

        # add aggregation clause
        body['aggs'] = self._aggs_body
        es_res = requests.post(self._query_url, data=json.dumps(body))
        res.status = getattr(falcon, 'HTTP_%s' % es_res.status_code)

        LOG.debug('Query to ElasticSearch returned: %s' % es_res.status_code)
        if es_res.status_code == 200:
            # convert the response into monasca metrics format
            aggs = es_res.json()['aggregations']

            flag = {'is_first': True}

            def _fixup_obj(obj):
                target = {'name': obj['name']}
                del obj['name']
                target['dimensions'] = obj
                if flag['is_first']:
                    flag['is_first'] = False
                    return json.dumps(target)
                else:
                    return ',' + json.dumps(target)

            def _make_body(obj, parent):
                for key in parent:
                    if key in ['key', 'doc_count']:
                        continue
                    if parent[key]['buckets']:
                        for bucket in parent[key]['buckets']:
                            new_obj = copy.deepcopy(obj)
                            new_obj[key] = bucket['key']
                            if bucket:
                                yield ''.join(_make_body(new_obj, bucket))
                            else:
                                yield _fixup_obj(new_obj)
                    else:
                        yield _fixup_obj(obj)

            res.stream = '[' + ''.join(_make_body({}, aggs)) + ']'
            res.content_type = 'application/json;charset=utf-8'
        else:
            res.stream = ''

    @resource_api.Restify('/v2.0/metrics/', method='post')
    def do_post_metrics(self, req, res):
        self.post_data(req, res)

    @resource_api.Restify('/v2.0/metrics/measurements', method='get')
    def do_get_measurements(self, req, res):
        LOG.debug('The metrics measurements GET request is received!')
        body = copy.deepcopy(self._query_body)
        self._handle_req_name(req, body)
        self._handle_req_dimensions(req, body)
        self._handle_req_start_time(req, body)

        # if there is no name or dimension, we do not need filter clause
        if not body['query']['filtered']['filter']['bool']['must']:
            del body['query']

        body['sort'] = self._sort_clause
        es_res = requests.post(self._query_url, data=json.dumps(body))
        res.status = getattr(falcon, 'HTTP_%s' % es_res.status_code)

        LOG.debug('Query to ElasticSearch returned: %s' % es_res.status_code)
        if es_res.status_code == 200:
            # convert the response into monasca metrics format
            items = es_res.json()['hits']['hits']

            flag = {'is_first': True}

            obj_columns = ["id", "timestamp", "value"]

            def _fixup_obj(obj, measures):
                if not obj:
                    return ''

                target = obj
                target['columns'] = obj_columns
                target['measurements'] = measures
                if flag['is_first']:
                    flag['is_first'] = False
                    return json.dumps(target)
                else:
                    return ',' + json.dumps(target)

            def _make_body(items):
                obj = {}
                measures = []
                for item in items:
                    source = item['_source']
                    new_obj = {'name': source['name'],
                               'dimensions': source['dimensions']}
                    if obj == new_obj:
                        measures.append([item['_id'],
                                         source['timestamp'],
                                         source['value']])
                    else:
                        yield _fixup_obj(obj, measures)
                        obj = new_obj
                        measures = [[item['_id'],
                                     source['timestamp'],
                                     source['value']]]
                yield _fixup_obj(obj, measures)

            res.stream = '[' + ''.join(_make_body(items)) + ']'
            res.content_type = 'application/json;charset=utf-8'
        else:
            res.stream = ''

    @resource_api.Restify('/v2.0/metrics/statistics', method='get')
    def do_get_statistics(self, req, res):
        res.status = getattr(falcon, 'HTTP_501')