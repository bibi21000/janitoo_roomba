# -*- coding: utf-8 -*-

"""Unittests for Janitoo-Roomba Server.
"""
__license__ = """
    This file is part of Janitoo.

    Janitoo is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Janitoo is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Janitoo. If not, see <http://www.gnu.org/licenses/>.

"""
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'
__copyright__ = "Copyright © 2013-2014-2015 Sébastien GALLET aka bibi21000"

import sys, os
import time, datetime
import unittest
import threading
import logging
from pkg_resources import iter_entry_points

from janitoo_nosetests.server import JNTTServer, JNTTServerCommon
from janitoo_nosetests.thread import JNTTThread, JNTTThreadCommon

from janitoo.utils import json_dumps, json_loads
from janitoo.utils import HADD_SEP, HADD
from janitoo.utils import TOPIC_HEARTBEAT
from janitoo.utils import TOPIC_NODES, TOPIC_NODES_REPLY, TOPIC_NODES_REQUEST
from janitoo.utils import TOPIC_BROADCAST_REPLY, TOPIC_BROADCAST_REQUEST
from janitoo.utils import TOPIC_VALUES_USER, TOPIC_VALUES_CONFIG, TOPIC_VALUES_SYSTEM, TOPIC_VALUES_BASIC

from janitoo_roomba.server import RoombaServer

##############################################################
#Check that we are in sync with the official command classes
#Must be implemented for non-regression
from janitoo.classes import COMMAND_DESC

COMMAND_DISCOVERY = 0x5000
COMMAND_ROOMBA_VACUUM = 0x2000

assert(COMMAND_DESC[COMMAND_ROOMBA_VACUUM] == 'COMMAND_ROOMBA_VACUUM')
assert(COMMAND_DESC[COMMAND_DISCOVERY] == 'COMMAND_DISCOVERY')
##############################################################

class TestRoombaSerser(JNTTServer, JNTTServerCommon):
    """Test the Roomba server
    """
    loglevel = logging.DEBUG
    path = '/tmp/janitoo_test'
    broker_user = 'toto'
    broker_password = 'toto'
    server_class = RoombaServer
    server_conf = "/opt/janitoo/src/janitoo_roomba/tests/data/janitoo_roomba.conf"

    def test_110_request_system_values(self):
        self.start()
        nodeHADD=HADD%(21,0)
        self.assertHeartbeatNode(hadd=nodeHADD)
        clientHADD=HADD%(5,0)
        self.assertNodeRequest(cmd_class=COMMAND_DISCOVERY, uuid='request_info_nodes', node_hadd=nodeHADD, client_hadd=clientHADD)
        self.assertBroadcastRequest(cmd_class=COMMAND_DISCOVERY, uuid='request_info_nodes', client_hadd=clientHADD)
        self.stop()

    def test_200_request_system_values(self):
        self.start()
        nodeHADD=HADD%(21,1)
        self.assertHeartbeatNode(hadd=nodeHADD)
        clientHADD=HADD%(5,0)
        self.assertNodeRequest(cmd_class=COMMAND_DISCOVERY, uuid='request_info_nodes', node_hadd=nodeHADD, client_hadd=clientHADD)
        self.assertBroadcastRequest(cmd_class=COMMAND_DISCOVERY, uuid='request_info_nodes', client_hadd=clientHADD)
        self.stop()

    def test_210_buttons(self):
        self.start()
        nodeHADD=HADD%(21,1)
        self.assertHeartbeatNode(hadd=nodeHADD)
        clientHADD=HADD%(5,0)
        self.assertNodeRequest(cmd_class=COMMAND_ROOMBA_VACUUM, uuid='buttons', data='clean', node_hadd=nodeHADD, client_hadd=clientHADD, genre=0x02, is_writeonly=True)
        time.sleep(10)
        self.assertNodeRequest(cmd_class=COMMAND_ROOMBA_VACUUM, uuid='buttons', data='clean', node_hadd=nodeHADD, client_hadd=clientHADD, genre=0x02, is_writeonly=True)
        time.sleep(2)
        self.assertNodeRequest(cmd_class=COMMAND_ROOMBA_VACUUM, uuid='buttons', data='dock', node_hadd=nodeHADD, client_hadd=clientHADD, genre=0x02, is_writeonly=True)
        self.stop()

class TestRoombaThread(JNTTThread, JNTTThreadCommon):
    """Test the Roomba server
    """
    thread_name = "roomba"

