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

import datetime
from oslo.config import cfg
import requests
import ujson as json

from monasca.common import strategy
from monasca.openstack.common import log


OPTS = [
    cfg.StrOpt('uri',
               help='Address to kafka server. For example: '
               'uri=http://192.168.1.191:9200/'),
    cfg.StrOpt('index_prefix',
               default='monasca_',
               help='The prefix for an index.'),
    cfg.StrOpt('doc_type',
               default='metrics',
               help='The type of the data.'),
    cfg.StrOpt('time_id',
               default='timestamp',
               help='The type of the data.'),
    cfg.BoolOpt('drop_data',
                default=False,
                help=('Specify if received data should be simply dropped. '
                      'This parameter is only for testing purposes.')),
]

cfg.CONF.register_opts(OPTS, group="es")

LOG = log.getLogger(__name__)


class ESConnection(object):

    def __init__(self):
        if not cfg.CONF.es.uri:
            raise Exception('ElasticSearch is not configured correctly! '
                            'Use configuration file to specify ElasticSearch '
                            'uri, for example: '
                            'uri=192.168.1.191:9200')

        self.uri = cfg.CONF.es.uri
        if self.uri.strip()[-1] != '/':
            self.uri += '/'
        self.index_prefix = cfg.CONF.es.index_prefix
        self.doc_type = cfg.CONF.es.doc_type
        self.time_id = cfg.CONF.es.time_id
        self.drop_data = cfg.CONF.es.drop_data

        self._index_strategy = strategy.IndexStrategy()
        LOG.debug('ElasticSearch Connection initialized successfully!')

    def send_messages(self, msg):
        LOG.debug('Prepare to send messages.')
        if self.drop_data:
            return
        else:
            msg = json.loads(msg)
            day = msg.get(self.time_id)
            if not day:
                day = datetime.datetime.now(0)
                msg[self.time_id] = day
            index = self._index_strategy.get_index(day)
            path = '%s%s%s/%s' % (self.uri, self.index_prefix, index,
                                  self.doc_type)
            LOG.debug('The post path:' + path)
            res = requests.post(path, data=json.dumps(msg))
            LOG.debug(res)