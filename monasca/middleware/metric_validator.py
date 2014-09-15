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


import StringIO
try:
    import ujson as json
except ImportError:
    import json


class MetricValidator(object):
    """middleware that validate the metric input stream.

    This middleware checks if the input stream actually follows metric spec
    and all the messages in the request has valid metric data. If the body
    is valid json and compliant with the spec, then the request will forward
    the request to the next in the pipeline, otherwise, it will reject the
    request with response code of 400 or 406.
    """
    def __init__(self, app, conf):
        self.app = app
        self.conf = conf

    def _is_valid_metric(self, metric):
        """Validate a message

        The current valid message format is as follows:
        {
            "metric": {"something": "The metric as a JSON object"},
            "meta": {
                "tenantId": "the tenant ID acquired",
                "region": "the region that the metric was submitted under",
            },
            "creation_time": "the time when the API received the metric",
            "value": "some value"
        }
        """
        if (metric.get('metric') and metric.get('meta') and
                metric.get('creation_time') and metric.get('value')):
            return True
        else:
            return False

    def __call__(self, environ, start_response):
        # if request starts with /datapoints/, then let it go on.
        # this login middle
        if (environ.get('PATH_INFO', '').startswith('/v2.0/metrics') and
                environ.get('REQUEST_METHOD', '') == 'POST'):
            # We only check the requests which are posting against metrics
            # endpoint
            try:
                body = environ['wsgi.input'].read()
                metrics = json.loads(body)
                # Do business logic validation here.
                is_valid = True
                if isinstance(metrics, list):
                    for metric in metrics:
                        if not self._is_valid_metric(metric):
                            is_valid = False
                            break
                else:
                    is_valid = self._is_valid_metric(metrics)

                if is_valid:
                    environ['wsgi.input'] = StringIO.StringIO(body)
                    return self.app(environ, start_response)
            except Exception:
                pass
            # It is either invalid or exceptioned out while parsing json
            # we will send the request back with 400.
            start_response("400 Bad Request", [], '')
            return []
        else:
            # not a metric post request, move on.
            return self.app(environ, start_response)


def filter_factory(global_conf, **local_conf):

    def validator_filter(app):
        return MetricValidator(app, local_conf)

    return validator_filter
