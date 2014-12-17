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
from stevedore import driver

from monasca.openstack.common import log
from monasca.openstack.common import service as os_service
from monasca import service

SERVICE_NAMESPACE = 'monasca.microservice'

OPTS = [
    cfg.StrOpt('service',
               help='Monasca micro services to process data.'),
    cfg.IntOpt('threads', default=1,
               help='The number of threads for the service.'),
]
cfg.CONF.register_opts(OPTS)

LOG = log.getLogger(__name__)


def main():
    service.prepare_service()
    if not cfg.CONF.service:
        LOG.error('No micro service is configured, please specify service '
                  'in the configuration file.')
        return None

    launcher = os_service.ServiceLauncher()

    # Now load the micro service
    service_driver = driver.DriverManager(
        SERVICE_NAMESPACE,
        cfg.CONF.service,
        invoke_on_load=True,
        invoke_kwds={'threads': cfg.CONF.threads})

    if not service_driver.driver:
        LOG.error('Failed loading micro service under name space %s.%s' %
                  (SERVICE_NAMESPACE, cfg.CONF.service))
        return None

    LOG.debug("Micro service %s is now loaded." %
              service_driver.driver.__class__.__name__)

    # now launch the service
    launcher.launch_service(service_driver.driver)
    launcher.wait()