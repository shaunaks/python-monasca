#!/usr/bin/python
# Copyright 2014 IBM Corp
#
# Author: Tong Li <litong01@us.ibm.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# this script will create a set of metrics at the endpoint specified as the
# program parameter
#
#
import datetime
import json
import random
import requests
import string
import sys


MOLD = {"name": "name1",
        "dimensions": {
            "key1": "value1",
            "key2": "value2"},
        "timestamp": '2014-12-01',
        "value": 100
        }


def setup_metrics(argv):

    # Generate unique 100 metrics
    for i in range(100):
        name = ''.join(random.sample(string.ascii_uppercase * 6, 6))
        MOLD['name'] = name
        # Generate 10 metrics for each name
        for j in range(10):
            MOLD['dimensions'] = {'key1': i * j, 'key2': j,
                                  'rkey%s' % j: j}
            MOLD['timestamp'] = str(datetime.datetime.now())
            MOLD['value'] = i * j * random.random()
            requests.post(argv[1], data=json.dumps(MOLD))


if __name__ == '__main__':
    if len(sys.argv) == 2:
        setup_metrics(sys.argv)
    else:
        print('Usage: setup_metrics endpoint. For example:')
        print('       setup_metrics http://host:9000/v2.0/metrics')
