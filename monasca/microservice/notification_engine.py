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

from oslo.config import cfg
from stevedore import driver

from monasca.common import es_conn
from monasca.common import kafka_conn
from monasca.openstack.common import log
from monasca.openstack.common import service as os_service

PROCESSOR_NAMESPACE = 'monasca.message.processor'
STRATEGY_NAMESPACE = 'monasca.index.strategy'

es_opts = [
    cfg.StrOpt('topic',
               default='alarm',
               help=('The topic that messages will be retrieved from.'
                     'This also will be used as a doc type when saved '
                     'to ElasticSearch.')),
    cfg.StrOpt('topic_notification_methods',
               default='notification_methods',
               help=('The topic that messages will be retrieved from.'
                     'This also will be used as a doc type when saved '
                     'to ElasticSearch.')),
    cfg.StrOpt('index_strategy', default='fixed',
               help='The index strategy used to create index name.'),
    cfg.StrOpt('index_prefix', default='data_',
               help='The index prefix where metrics were saved to.'),
    cfg.StrOpt('doc_type',
               default='',
               help=('The document type which defines what document '
                     'type the messages will be save into. If not '
                     'specified, then the topic will be used.')),
    cfg.StrOpt('processor',
               default='',
               help=('The message processer to load to process the message.'
                     'If the message does not need to be process anyway,'
                     'leave the default')),
]

es_group = cfg.OptGroup(name='notification', title='notification')
cfg.CONF.register_group(es_group)
cfg.CONF.register_opts(es_opts, es_group)

LOG = log.getLogger(__name__)


class NotificationEngine(os_service.Service):

    def __init__(self, threads=1000):
        super(NotificationEngine, self).__init__(threads)
        self._kafka_conn = kafka_conn.KafkaConnection(
            cfg.CONF.notification.topic)
        self.topic = cfg.CONF.notification.topic_notification_methods

        # load index strategy
        if cfg.CONF.notification.index_strategy:
            self.index_strategy = driver.DriverManager(
                STRATEGY_NAMESPACE,
                cfg.CONF.notification.index_strategy,
                invoke_on_load=True,
                invoke_kwds={}).driver
            LOG.debug(dir(self.index_strategy))
        else:
            self.index_strategy = None

        self.index_prefix = cfg.CONF.notification.index_prefix

        self._es_conn = es_conn.ESConnection(
            self.topic, self.index_strategy, self.index_prefix)

        if cfg.CONF.notification.processor:
            self.notification_processor = driver.DriverManager(
                PROCESSOR_NAMESPACE,
                cfg.CONF.notification.processor,
                invoke_on_load=True,
                invoke_kwds={}).driver
            LOG.debug(dir(self.notification_processor))
        else:
            self.notification_processor = None

    def start(self):
        while True:
            try:
                for msg in self._kafka_conn.get_messages():
                    (self.notification_processor.
                        handle_alarm_msg(self._es_conn, msg))

                # if autocommit is set, this will be a no-op call.
                self._kafka_conn.commit()
            except Exception:
                LOG.exception('Error occurred while handling kafka messages.')

    def stop(self):
        self._kafka_conn.close()
        super(NotificationEngine, self).stop()
