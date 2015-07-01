# -*- coding: utf-8 -*-
# Copyright 2015 Carnegie Mellon University
# Author: Yihan Wang <wangff9@gmail.com>
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

import json
from monasca.common import alarm_expr_validator as validator
from monasca.openstack.common import log
from monasca import tests


LOG = log.getLogger(__name__)


class TestAlarmExprCalculator(tests.BaseTestCase):
    def __init__(self, *args, **kwargs):
        super(TestAlarmExprCalculator, self).__init__(*args, **kwargs)
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
        self.alarm_definition0_wrong0 = json.dumps({
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
            ]})
        self.alarm_definition0_wrong1 = json.dumps({
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
                "or sum(biz=5{dn5=dv58}) >9 9and "
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
        self.alarm_definition1_update_wrong0 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "min(biz{key2=value1})<1450",
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
        self.alarm_definition1_update_wrong1 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "min(biz{key2=value2})<1450",
            "match_by": [
                "os"
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
        self.alarm_definition1_update_wrong2 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "min(biz{key2=value2})<1450 and max(baz)<500",
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
        self.alarm_definition1_update_wrong3 = json.dumps({
            "id": "f9935bcc-9641-4cbf-8224-0993a947ea83",
            "name": "Average CPU percent greater than 10",
            "description":
                "The average CPU percent is greater than 10",
            "expression": "min(baz{key2=value2})<1450",
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

    def setUp(self):
        super(TestAlarmExprCalculator, self).setUp()

    def test_is_valid_alarm_definition(self):
        self.assertEqual(True, validator.is_valid_alarm_definition(
            self.alarm_definition1))
        self.assertEqual(True, validator.is_valid_alarm_definition(
            self.alarm_definition0))
        self.assertEqual(True, validator.is_valid_alarm_definition(
            self.alarm_definition1_update))
        self.assertEqual(True, validator.is_valid_alarm_definition(
            self.alarm_definition1_update_wrong0))
        self.assertEqual(False, validator.is_valid_alarm_definition(
            self.alarm_definition0_wrong0))
        self.assertEqual(False, validator.is_valid_alarm_definition(
            self.alarm_definition0_wrong1))
        self.assertEqual(True, validator.is_valid_alarm_definition(
            self.alarm_definition1_update_wrong1))

    def test_is_valid_update_alarm_definition(self):
        self.assertEqual(True, validator.is_valid_update_alarm_definition(
            self.alarm_definition1, self.alarm_definition1_update))
        self.assertEqual(False, validator.is_valid_update_alarm_definition(
            self.alarm_definition1, self.alarm_definition0_wrong0))
        self.assertEqual(False, validator.is_valid_update_alarm_definition(
            self.alarm_definition1, self.alarm_definition1_update_wrong0))
        self.assertEqual(False, validator.is_valid_update_alarm_definition(
            self.alarm_definition1, self.alarm_definition1_update_wrong1))
        self.assertEqual(False, validator.is_valid_update_alarm_definition(
            self.alarm_definition1, self.alarm_definition1_update_wrong2))
        self.assertEqual(False, validator.is_valid_update_alarm_definition(
            self.alarm_definition1, self.alarm_definition1_update_wrong3))