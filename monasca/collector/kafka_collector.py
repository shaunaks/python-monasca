#
# Copyright 2012-2013 eNovance <licensing@enovance.com>
#
# Author: Julien Danjou <julien@danjou.info>
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

from monasca.common import kafka_conn
from monasca.common import es_conn
from monasca.openstack.common import log
from monasca.openstack.common import service as os_service
from monasca import service

LOG = log.getLogger(__name__)


class KafkaCollector(os_service.Service):

    def __init__(self, threads=1000):
        super(KafkaCollector, self).__init__(threads)
        self._kafka_conn = kafka_conn.KafkaConnection()
        self._es_conn = es_conn.ESConnection()

    def start(self):
        while True:
            try:
                for message in self._kafka_conn.get_messages():
                    LOG.debug(message.message.value)
                    self._es_conn.send_messages(message.message.value)
                # if autocommit is set, this will be a no-op call.
                self._kafka_conn.commit()
            except Exception:
                LOG.exception('Error occurred while handling kafka messages.')

    def stop(self):
        self._kafka_conn.close()
        super(KafkaCollector, self).stop()


def main():
    service.prepare_service()
    launcher = os_service.ServiceLauncher()
    launcher.launch_service(KafkaCollector())
    launcher.wait()