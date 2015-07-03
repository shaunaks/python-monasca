# -*- coding: utf-8 -*-
# Copyright 2015 Carnegie Mellon University
# Author: Yihan Wang <wangff9@gmail.com>
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

import json
from monasca.microservice import thresholding_processor as processor
from monasca.openstack.common import log
from monasca.openstack.common import timeutils as tu
from monasca import tests

LOG = log.getLogger(__name__)


class TestThresholdingProcessor(tests.BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(TestThresholdingProcessor, self).__init__(*args, **kwargs)
        self.alarm_definition0 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression":
                "max(-_.千幸福的笑脸{घोड़ा=馬,  "
                "dn2=dv2,"
                "千幸福的笑脸घ=千幸福的笑脸घ}) gte 100 "
                "times 1 And "
                "(min(ເຮືອນ{dn3=dv3,家=дом}) < 10 "
                "or sum(biz{dn5=dv58}) >9 9and "
                "count(fizzle) lt 0 or count(baz) > 1)",
            "match_by": [],
            "severity": "LOW",
            "ok_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "alarm_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "undetermined_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ]})
        self.alarm_definition1 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "max(biz{key2=value2})>1400",
            "match_by": [
                "hostname"
            ],
            "severity": "LOW",
            "ok_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "alarm_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "undetermined_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ]})
        self.alarm_definition1_update = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "min(biz{key2=value2})<1450",
            "match_by": [
                "hostname"
            ],
            "severity": "LOW",
            "ok_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "alarm_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "undetermined_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ]})
        self.alarm_definition4 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "avg(biz{key2=value2})>1400",
            "match_by": [
                "hostname"
            ],
            "severity": "LOW",
            "ok_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "alarm_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "undetermined_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ]})
        self.alarm_definition2 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "max(foo)>=100 times 4",
            "match_by": [],
            "severity": "LOW",
            "ok_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "alarm_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "undetermined_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ]})
        self.alarm_definition2_update = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "max(foo,80)>=100 times 6",
            "match_by": [],
            "severity": "LOW",
            "ok_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "alarm_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "undetermined_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ]})
        self.alarm_definition3 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "max(foo{hostname=mini-mon"
                          ",千=千}, 120)"
                          " = 100 and (max(bar)>100 "
                          " or max(biz)>100)",
            "match_by": [],
            "severity": "LOW",
            "ok_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "alarm_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "undetermined_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ]})
        self.alarm_definition5 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "avg(biz{key2=value2})>1400",
            "match_by": [
                "hostname",
                "system"
            ],
            "severity": "LOW",
            "ok_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "alarm_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ],
            "undetermined_actions": [
                "c60ec47e-5038-4bf1-9f95-4046c6e9a759"
            ]})

    def get_metric2_0(self):
        list = []
        for i in range(0, 10, 1):
            metrics = {"name": "foo",
                       "dimensions": {
                           "key1": "value1",
                           "key2": "value2"
                       },
                       "timestamp":
                           tu.iso8601_from_timestamp(
                               tu.utcnow_ts() + i * 20 - 140),
                       "value": i * 10}
            list.append(json.dumps(metrics))
        return list

    def get_metric2_1(self):
        list = []
        for i in range(10, 30, 1):
            metrics = {"name": "foo",
                       "dimensions": {
                           "key1": "value1",
                           "key2": "value2"
                       },
                       "timestamp":
                           tu.iso8601_from_timestamp(
                               tu.utcnow_ts() + i * 20 - 570),
                       "value": i * 75}
            list.append(json.dumps(metrics))
        return list

    def get_metric2_2(self):
        list = []
        for i in range(0, 10, 1):
            metrics = {"name": "foo",
                       "dimensions": {
                           "key1": "value1",
                           "key2": "value2"
                       },
                       "timestamp":
                           tu.iso8601_from_timestamp(
                               tu.utcnow_ts() + i * 20 - 140),
                       "value": i * 10 + 200}
            list.append(json.dumps(metrics))
        return list

    def get_metric1(self):
        list = []
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key2": "value2"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1300}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key1": "value1",
                       "key2": "value2",
                       "key3": "value3"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1500}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h2",
                       "key2": "value2"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1500}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h3",
                       "key2": "value2"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1200}
        list.append(json.dumps(metrics))
        return list

    def get_metric4(self):
        list = []
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key2": "value2"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts() - 200),
                   "value": 1300}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key2": "value2",
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts() - 30),
                   "value": 1200}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key1": "value1",
                       "key2": "value2",
                       "key3": "value3"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1601}
        list.append(json.dumps(metrics))
        return list

    def get_metric5(self):
        list = []
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key2": "value2"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 2000}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "system": "windows",
                       "key2": "value2"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1300}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "system": "linux",
                       "key2": "value2",
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts() - 30),
                   "value": 1200}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "system": "windows",
                       "key1": "value1",
                       "key2": "value2",
                       "key3": "value3"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1601}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h2",
                       "system": "linux",
                       "key1": "value1",
                       "key2": "value2",
                       "key3": "value3"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1601}
        list.append(json.dumps(metrics))
        return list

    def get_metric0(self):
        list = []
        metrics = {"name": "baz",
                   "dimensions": {
                       "घोड़ा": "馬",
                       "dn2": "dv2",
                       "千幸福的笑脸घ": "千幸福的笑脸घ"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1500}
        list.append(json.dumps(metrics))
        metrics = {"name": "-_.千幸福的笑脸",
                   "dimensions": {
                       "घोड़ा": "馬",
                       "dn2": "dv2",
                       "千幸福的笑脸घ": "千幸福的笑脸घ"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1500}
        list.append(json.dumps(metrics))
        metrics = {"name": "ເຮືອນ",
                   "dimensions": {
                       "dn3": "dv3",
                       "家": "дом"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 5}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "dn5": "dv58"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 5}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "dn5": "dv58"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 95}
        list.append(json.dumps(metrics))
        return list

    def get_metric_wrong_1(self):
        list = []
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key2": "value2"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1300}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key1": "value1",
                       "key2": "value2",
                       "key3": "value3"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts())}
        list.append(json.dumps(metrics))
        return list

    def get_metric_not_match(self):
        list = []
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key2": "value2"
                   },
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts()),
                   "value": 1300}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key1": "value1",
                       "key3": "value3"
                   },
                   'value': 15000,
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts())}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "hostname": "h1",
                       "key2": "value1",
                       "key3": "value3"
                   },
                   'value': 15000,
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts())}
        list.append(json.dumps(metrics))
        metrics = {"name": "biz",
                   "dimensions": {
                       "key2": "value1",
                       "key3": "value3"
                   },
                   'value': 15000,
                   "timestamp":
                       tu.iso8601_from_timestamp(tu.utcnow_ts())}
        list.append(json.dumps(metrics))
        return list

    def setUp(self):
        super(TestThresholdingProcessor, self).setUp()

    def test__init_(self):
        """Test processor _init_.

        If alarm definition is not in standard format,
        the processor cannot be successfully initialized.
        Alarm_definition3 is a bad one.
        Processor _init_ will fail on this case.
        """
        tp = None
        try:
            tp = processor.ThresholdingProcessor(self.alarm_definition0)
        except Exception:
            tp = None
        self.assertIsInstance(tp, processor.ThresholdingProcessor)
        try:
            tp = processor.ThresholdingProcessor(self.alarm_definition1)
        except Exception:
            tp = None
        self.assertIsInstance(tp, processor.ThresholdingProcessor)
        try:
            tp = processor.ThresholdingProcessor(self.alarm_definition2)
        except Exception:
            tp = None
        self.assertIsInstance(tp, processor.ThresholdingProcessor)
        try:
            tp = processor.ThresholdingProcessor(self.alarm_definition3)
        except Exception:
            tp = None
        self.assertIsNone(tp)

    def test_process_alarms(self):
        """Test if alarm is correctly produced."""

        # test utf8 dimensions and compound logic expr
        # init processor
        tp = processor.ThresholdingProcessor(self.alarm_definition0)
        # send metrics to the processor
        metrics_list = self.get_metric0()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        # manually call the function to update alarms
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(1, len(alarms))
        self.assertEqual('ALARM', json.loads(alarms[0])['state'])

        # test more than 1 periods
        tp = processor.ThresholdingProcessor(self.alarm_definition0)
        metrics_list = self.get_metric0()
        for metrics in metrics_list[0:2]:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(0, len(alarms))
        self.assertEqual('UNDETERMINED', tp.expr_data_queue[None]['state'])
        tp = processor.ThresholdingProcessor(self.alarm_definition2)
        metrics_list = self.get_metric2_0()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(1, len(alarms))
        self.assertEqual('OK', json.loads(alarms[0])['state'])
        tp = processor.ThresholdingProcessor(self.alarm_definition2)
        metrics_list = self.get_metric2_1()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(1, len(alarms))
        self.assertEqual('ALARM', json.loads(alarms[0])['state'])
        print (json.loads(alarms[0])['sub_alarms'][0]['current_values'])
        tp = processor.ThresholdingProcessor(self.alarm_definition2)
        metrics_list = self.get_metric2_2()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(0, len(alarms))

        # test alarms with match_up
        tp = processor.ThresholdingProcessor(self.alarm_definition1)
        metrics_list = self.get_metric1()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(3, len(alarms))
        self.assertEqual('ALARM', tp.expr_data_queue['h1,']['state'])
        self.assertEqual('ALARM', tp.expr_data_queue['h2,']['state'])
        self.assertEqual('OK', tp.expr_data_queue['h3,']['state'])

        # test alarms with multiple match_ups
        tp = processor.ThresholdingProcessor(self.alarm_definition5)
        metrics_list = self.get_metric5()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(3, len(alarms))

        # test alarms with metrics having more dimensions
        tp = processor.ThresholdingProcessor(self.alarm_definition4)
        metrics_list = self.get_metric4()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(1, len(alarms))
        self.assertEqual(1, len(json.loads(alarms[0])['metrics']))
        print (json.loads(alarms[0])['sub_alarms'][0]['current_values'])
        self.assertEqual('ALARM', json.loads(alarms[0])['state'])

        # test when receiving wrong format metrics
        tp = processor.ThresholdingProcessor(self.alarm_definition1)
        metrics_list = self.get_metric_wrong_1()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(1, len(alarms))
        self.assertEqual([1300],
                         json.loads(alarms[0])
                         ['sub_alarms'][0]['current_values'])

        # test when received metrics dimension not match
        tp = processor.ThresholdingProcessor(self.alarm_definition1)
        alarms = tp.process_alarms()
        print (alarms)
        metrics_list = self.get_metric_not_match()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual('OK', json.loads(alarms[0])['state'])

        # test a success update alarm definition
        tp = processor.ThresholdingProcessor(self.alarm_definition1)
        metrics_list = self.get_metric1()
        for metrics in metrics_list:
            tp.process_metrics(metrics)
        alarms = tp.process_alarms()
        print (alarms)
        re = tp.update_thresh_processor(self.alarm_definition1_update)
        self.assertEqual(True, re)
        alarms = tp.process_alarms()
        print (alarms)
        self.assertEqual(3, len(alarms))
        tp = processor.ThresholdingProcessor(self.alarm_definition2)
        re = tp.update_thresh_processor(self.alarm_definition2_update)
        self.assertEqual(True, re)
