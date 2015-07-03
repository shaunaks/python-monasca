# Copyright 2012-2013 eNovance <licensing@enovance.com>
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

from oslo.config import cfg
import requests
import ujson as json

from monasca.openstack.common import log


ES_OPTS = [
    cfg.StrOpt('uri',
               help='Address to kafka server. For example: '
               'uri=http://192.168.1.191:9200/'),
    cfg.StrOpt('time_id',
               default='timestamp',
               help='The type of the data.'),
    cfg.BoolOpt('drop_data',
                default=False,
                help=('Specify if received data should be simply dropped. '
                      'This parameter is only for testing purposes.')),
]

cfg.CONF.register_opts(ES_OPTS, group="es_conn")

LOG = log.getLogger(__name__)


class ESConnection(object):

    def __init__(self, doc_type, index_stratey, index_prefix):
        if not cfg.CONF.es_conn.uri:
            raise Exception('ElasticSearch is not configured correctly! '
                            'Use configuration file to specify ElasticSearch '
                            'uri, for example: '
                            'uri=192.168.1.191:9200')

        self.uri = cfg.CONF.es_conn.uri
        if self.uri.strip()[-1] != '/':
            self.uri += '/'

        self.doc_type = doc_type
        self.index_strategy = index_stratey
        self.index_prefix = index_prefix

        self.time_id = cfg.CONF.es_conn.time_id
        self.drop_data = cfg.CONF.es_conn.drop_data

        self.search_path = '%s%s*/%s/_search' % (self.uri,
                                                 self.index_prefix,
                                                 self.doc_type)
        LOG.debug('ElasticSearch Connection initialized successfully!')

    def send_messages(self, msg):
        LOG.debug('Prepare to send messages.')
        if self.drop_data:
            return
        else:
            # index may change over the time, it has to be called for each
            # request
            index = self.index_strategy.get_index()
            path = '%s%s%s/%s/_bulk' % (self.uri, self.index_prefix,
                                        index, self.doc_type)
            res = requests.post(path, data=msg)
            LOG.debug('Msg posted with response code: %s' % res.status_code)
            return res.status_code

    def get_messages(self, cond):
        LOG.debug('Prepare to get messages.')
        if cond:
            data = json.dumps(cond)
        else:
            data = {}
        res = requests.post(self.search_path, data=data)
        return res.status_code