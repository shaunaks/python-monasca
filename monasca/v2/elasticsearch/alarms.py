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
from oslo.config import cfg
from stevedore import driver

from monasca.common import es_conn
from monasca.common import namespace
from monasca.common import resource_api
from monasca.openstack.common import log


ALARMS_OPTS = [
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


cfg.CONF.register_opts(ALARMS_OPTS, group='alarms')

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

    @resource_api.Restify('/v2.0/alarms/', method='get')
    def do_get_alarms(self, req, res):
        LOG.debug('Getting existing alarms')
        # TODO(STUDENTS) implement the logic to get alarms from back store
        res.status = getattr(falcon, 'HTTP_200')