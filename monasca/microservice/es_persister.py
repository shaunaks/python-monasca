#
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

from oslo.config import cfg
from stevedore import driver

from monasca.common import es_conn
from monasca.common import kafka_conn
from monasca.openstack.common import log
from monasca.openstack.common import service as os_service


PROCESSOR_NAMESPACE = 'monasca.message.processor'

es_opts = [
    cfg.StrOpt('topic',
               default='metrics',
               help=('The topic that messages will be retrieved from.'
                     'This also will be used as a doc type when saved '
                     'to ElasticSearch.')),
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

es_group = cfg.OptGroup(name='es_persister', title='es_persister')
cfg.CONF.register_group(es_group)
cfg.CONF.register_opts(es_opts, es_group)

LOG = log.getLogger(__name__)


class ESPersister(os_service.Service):

    def __init__(self, threads=1000):
        super(ESPersister, self).__init__(threads)
        self._kafka_conn = kafka_conn.KafkaConnection(
            cfg.CONF.es_persister.topic)

        # Use doc_type if it is defined.
        if cfg.CONF.es_persister.doc_type:
            self._es_conn = es_conn.ESConnection(
                cfg.CONF.es_persister.doc_type)
        else:
            self._es_conn = es_conn.ESConnection(
                cfg.CONF.es_persister.topic)

        if cfg.CONF.es_persister.processor:
            self.msg_processor = driver.DriverManager(
                PROCESSOR_NAMESPACE,
                cfg.CONF.es_persister.processor,
                invoke_on_load=True,
                invoke_kwds={}).driver
            LOG.debug(dir(self.msg_processor))
        else:
            self.msg_processor = None

    def start(self):
        while True:
            try:
                for msg in self._kafka_conn.get_messages():
                    if msg and msg.message:
                        LOG.debug(msg.message.value)
                        if self.msg_processor:
                            value = self.msg_processor.process_msg(
                                msg.message.value)
                        else:
                            value = msg.message.value
                        if value:
                            self._es_conn.send_messages(value)
                # if autocommit is set, this will be a no-op call.
                self._kafka_conn.commit()
            except Exception:
                LOG.exception('Error occurred while handling kafka messages.')

    def stop(self):
        self._kafka_conn.close()
        super(ESPersister, self).stop()