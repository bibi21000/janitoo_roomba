# -*- coding: utf-8 -*-
"""The Roomba Janitoo helper
It handle all communications to the Roomba vacuums



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
__copyright__ = "Copyright © 2013-2014-2015-2016 Sébastien GALLET aka bibi21000"

# Set default logging handler to avoid "No handler found" warnings.
import logging
logger = logging.getLogger(__name__)

import threading
import requests
import socket
import time
from datetime import datetime, timedelta

from janitoo.utils import json_loads
from janitoo.component import JNTComponent

##############################################################
#Check that we are in sync with the official command classes
#Must be implemented for non-regression
from janitoo.classes import COMMAND_DESC

COMMAND_METER = 0x0032
COMMAND_ROOMBA_VACUUM = 0x2000
COMMAND_ROOMBA_DRIVE = 0x2001

assert(COMMAND_DESC[COMMAND_METER] == 'COMMAND_METER')
assert(COMMAND_DESC[COMMAND_ROOMBA_VACUUM] == 'COMMAND_ROOMBA_VACUUM')
assert(COMMAND_DESC[COMMAND_ROOMBA_DRIVE] == 'COMMAND_ROOMBA_DRIVE')
##############################################################

from janitoo_roomba import OID

def make_roowifi(**kwargs):
    return RoombaRoowifi(**kwargs)

def make_roomba900(**kwargs):
    return Roomba900(**kwargs)

commands = {
    "clean":135,
    "dock":143,
    "full":132,
    "max":136,
    "play":141,
    "start":128,
    "spot":134,
    "LED_COMMAND":139,
    "SENSOR_COMMAND":142,
    "SENSOR_PACKET_0":0,
    "SENSOR_PACKET_1":1,
    "SENSOR_PACKET_2":2,
    "SENSOR_PACKET_3":3,
    "NUM_BYTES_PACKET_0":26,
    }

sensors = {
    "Bumps Wheeldrops":0,
    "Wall":0,
    "Cliff Left":0,
    "Cliff Front Left":0,
    "Cliff Front Right":0,
    "Cliff Right":0,
    "Virtual Wall":0,
    "Motor Overcurrents":0,
    "Dirt Detector - Left":0,
    "Dirt Detector - Right":0,
    "Remote Opcode":0,
    "Buttons":0,
    "Distance":0,
    "Angle":0,
    "State":0,
    "Voltage":0,
    "Current":0,
    "Temperature":0,
    "Charge":0,
    "Capacity":0,
    "Battery-level":0,
    }

states = {
    0:"Not charging",
    1:"Charging Recovery",
    2:"Charging",
    3:"Trickle charging",
    4:"Waiting",
    5:"Charging Error",
    6:"Cleaning",
    7:"Docking",
    8:"Maximun",
    }

class RoombaRoowifi(JNTComponent):
    """For roowifi
    """
    def __init__(self, bus=None, addr=None, **kwargs):
        """
        """
        oid = kwargs.pop('oid','%s.roowifi'%OID)
        name = kwargs.pop('name', "Roowifi series")
        product_name = kwargs.pop('product_name', "Roomba Vacuum")
        product_type = kwargs.pop('product_type', "Vacuum")
        JNTComponent.__init__(self, oid, bus=bus, addr=addr, name=name,
                product_name=product_name, product_type=product_type, **kwargs)
        logger.debug("[%s] - __init__ node uuid:%s", self.__class__.__name__, self.uuid)
        self._lock = threading.Lock()
        self._current = -1.0
        self._voltage = -1.0
        self._charge = -1.0
        self._capacity = -1.0
        self._battery = -1.0
        self._temperature = -1.0
        self._state = -1.0
        self.telemetry_ttl = 60
        self._telemetry_last = False
        self._telemetry_next_run = datetime.now() + timedelta(seconds=15)

        uuid = "current"
        self.values[uuid] = self.value_factory['sensor_current'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The dock current',
            label='Current',
            units='mA',
            get_data_cb=self.get_current,
        )
        poll_value = self.values[uuid].create_poll_value(default=60)
        self.values[poll_value.uuid] = poll_value

        uuid = "voltage"
        self.values[uuid] = self.value_factory['sensor_voltage'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The dock voltage',
            label='Voltage',
            units='V',
            get_data_cb=self.get_voltage,
        )
        poll_value = self.values[uuid].create_poll_value(default=60)
        self.values[poll_value.uuid] = poll_value

        uuid = "battery_current"
        self.values[uuid] = self.value_factory['sensor_current'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The current of the battery',
            label='Charge',
            units='mA',
            get_data_cb=self.get_battery_charge,
        )
        poll_value = self.values[uuid].create_poll_value(default=60)
        self.values[poll_value.uuid] = poll_value

        uuid = "battery_capacity"
        self.values[uuid] = self.value_factory['sensor_current'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The capacity of the battery',
            label='Capacity',
            units='mA',
            get_data_cb=self.get_battery_capacity,
        )
        poll_value = self.values[uuid].create_poll_value(default=60)
        self.values[poll_value.uuid] = poll_value

        uuid = "battery_percent"
        self.values[uuid] = self.value_factory['sensor_percent'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The percent charge of the battery',
            label='Percent',
            get_data_cb=self.get_battery_percent,
        )
        poll_value = self.values[uuid].create_poll_value(default=60)
        self.values[poll_value.uuid] = poll_value

        uuid = "ip_ping"
        self.values[uuid] = self.value_factory['ip_ping'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='Ping the vacuum',
            label='Ping',
        )
        config_value = self.values[uuid].create_config_value(help='The IP of the vacuum', label='IP',)
        self.values[config_value.uuid] = config_value
        poll_value = self.values[uuid].create_poll_value(default=60)
        self.values[poll_value.uuid] = poll_value

        uuid = "username"
        self.values[uuid] = self.value_factory['config_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='Username to connect the roomba',
            label='Username',
        )

        uuid = "password"
        self.values[uuid] = self.value_factory['config_password'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='Password to connect the roomba',
            label='Password',
        )

        uuid = "temperature"
        self.values[uuid] = self.value_factory['sensor_temperature'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The temperature of the roomba',
            label='Temperature',
            get_data_cb=self.get_temperature,
        )
        poll_value = self.values[uuid].create_poll_value(default=60)
        self.values[poll_value.uuid] = poll_value

        uuid = "dock"
        self.values[uuid] = self.value_factory['sensor_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The state of the roomba dock',
            label='Dock',
            get_data_cb=self.get_state,
        )
        poll_value = self.values[uuid].create_poll_value(default=60)
        self.values[poll_value.uuid] = poll_value

        uuid = "buttons"
        self.values[uuid] = self.value_factory['action_list'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The buttons on the roomba',
            label='Buttons',
            list_items=['clean', 'spot', 'dock', 'idle'],
            set_data_cb=self.set_button,
            is_writeonly = True,
            cmd_class = COMMAND_ROOMBA_VACUUM,
        )

        uuid = "drive"
        self.values[uuid] = self.value_factory['action_list'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='Drive the roomba to a position',
            label='Drive',
            list_items=['0', '1', '2', '3', '4', '5', 'dock'],
            set_data_cb=self.set_drive,
            is_writeonly = True,
            cmd_class = COMMAND_ROOMBA_DRIVE,
        )
        config_value = self.values[uuid].create_config_value(help='A list of tuples (velocity, radius, time) from dock positions', label='moves',)
        self.values[config_value.uuid] = config_value

    def check_heartbeat(self):
        """Check that the component is 'available'

        """
        #~ print "it's me %s : %s" % (self.values['upsname'].data, self._ups_stats_last)
        return self._telemetry_last

    def get_telemetry(self):
        """Roomba method which fetches telemetry data about the robot.

        Other values that can be implemented:

        - sensors['Bumps Wheeldrops'] = self.j['response']['r0']['value']
        - sensors['Wall'] = self.j['response']['r1']['value']
        - sensors['Cliff Left'] = self.j['response']['r2']['value']
        - sensors['Cliff Front Left'] = self.j['response']['r3']['value']
        - sensors['Cliff Front Right'] = self.j['response']['r4']['value']
        - sensors['Cliff Right'] = self.j['response']['r5']['value']
        - sensors['Virtual Wall'] = self.j['response']['r6']['value']
        - sensors['Motor Overcurrents'] = self.j['response']['r7']['value']
        - sensors['Dirt Detector - Left'] = self.j['response']['r8']['value']
        - sensors['Dirt Detector - Right'] = self.j['response']['r9']['value']
        - sensors['Remote Opcode'] = self.j['response']['r10']['value']
        - sensors['Buttons'] = self.j['response']['r11']['value']
        - sensors['Distance'] = self.j['response']['r12']['value']
        - sensors['Angle'] = self.j['response']['r13']['value']
        - sensors['State'] = State[int(self.j['response']['r14']['value'])]
        - sensors['Voltage'] = self.j['response']['r15']['value']
        - sensors['Current'] = self.j['response']['r16']['value']
        - sensors['Temperature'] = self.j['response']['r17']['value']
        - sensors['Charge'] = self.j['response']['r18']['value']
        - sensors['Capacity'] = self.j['response']['r19']['value']
        - sensors['battery-level'] =  int(self.j['response']['r18']['value'])*100 / int (self.j['response']['r19']['value'])
        """
        if self._telemetry_next_run < datetime.now():
            locked = self._lock.acquire(False)
            if locked == True:
                try:
                    auth = (self.values['username'].data, self.values['password'].data)
                    r = requests.get('http://' + self.values['ip_ping_config'].data + '/roomba.json', auth=auth)
                    self._telemetry = json_loads(r.text)
                    logger.debug("[%s] - retrieve telemetry : %s", self.__class__.__name__, self._telemetry)
                    self._temperature = float(self._telemetry['response']['r17']['value'])
                    self._charge = float(self._telemetry['response']['r18']['value'])
                    self._capacity = float(self._telemetry['response']['r19']['value'])
                    self._state = int(self._telemetry['response']['r14']['value'])
                    self._voltage = round(float(self._telemetry['response']['r15']['value'])/1000,2)
                    self._current = round(float(self._telemetry['response']['r16']['value']),2)
                    try:
                        self._battery = round(100.0 * self._charge / self._capacity, 2)
                    except ZeroDivisionError:
                        self._battery = -1.0
                    self._telemetry_last = True
                except Exception:
                    logger.exception("[%s] - Exception in get_telemetry", self.__class__.__name__)
                    self._telemetry_last = False
                finally:
                    self._lock.release()
                secs = self.values['ip_ping_poll'].data
                if secs < 0:
                    secs=60
                self._telemetry_next_run = datetime.now() + timedelta(seconds=secs)

    def get_battery_charge(self, node_uuid, index):
        """Return the battery
        """
        self.get_telemetry()
        return self._charge

    def get_battery_capacity(self, node_uuid, index):
        """Return the battery
        """
        self.get_telemetry()
        return self._capacity

    def get_battery_percent(self, node_uuid, index):
        """Return the battery charge
        """
        self.get_telemetry()
        return self._battery

    def get_temperature(self, node_uuid, index):
        """Return the temperture
        """
        self.get_telemetry()
        return self._temperature

    def get_current(self, node_uuid, index):
        """Return the current
        """
        self.get_telemetry()
        return self._current

    def get_voltage(self, node_uuid, index):
        """Return the voltage
        """
        self.get_telemetry()
        return self._voltage

    def get_state(self, node_uuid, index):
        """Return the dock state
        """
        self.get_telemetry()
        if self._state in states:
            return states[self._state]
        return "Unknown"

    def set_button(self, node_uuid, index, data):
        """Return the dock state
        """
        auth = (self.values['username'].data, self.values['password'].data)
        params = {}
        if data == "clean":
            params['exec'] = 4
        elif data == "spot":
            params['exec'] = 5
        elif data == "dock":
            params['exec'] = 6
        elif data == "idle":
            params['exec'] = 1
        r = requests.get('http://' + self.values['ip_ping_config'].data + '/rwr.cgi', params = params, auth=auth)

    def set_drive(self, node_uuid, index, data):
        """Drive the robot
        """
        pass

    def command(self, ip, port, device, command):
        """Other way to acces the roowifi using a simple tcp socket.
        A simple copy paste ... does not work
        """
        logger.debug("[%s] - Start processing clean Command on %s  ", self.__class__.__name__, device)
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            time.sleep(1)
            self.s.connect((ip , port))
            time.sleep(1)
            self.s.send(chr(132))
            time.sleep(1)
            #print("Le code de la fonction est %s  " % table[command])
            self.s.send(chr(table[command]))
            time.sleep(1)
            self.s.close()
            self._log.debug("%s command Success on %s" % (command,device))
            if str(command) == "clean":
                sensors['State'] = State[int(6)]
            if str(command) == "dock" :
                sensors['State'] =  State[int(7)]
            if str(command) == "max" :
                sensors['State'] =  State[int(8)]
            return True
        except Exception:
            logger.error("[%s] - %s Command Failed on %s", self.__class__.__name__, command)
            return False

class Roomba900(JNTComponent):
    """
    """
    def __init__(self, bus=None, addr=None, **kwargs):
        """ For roomba serie 900 using the irobot cloud
        From https://github.com/koalazak/dorita980
        """
        oid = kwargs.pop('oid','%s.roomba900'%OID)
        name = kwargs.pop('name', "Roomba 900 series")
        product_name = kwargs.pop('product_name', "Roomba Vacuum")
        product_type = kwargs.pop('product_type', "Vacuum")
        JNTComponent.__init__(self, oid, bus=bus, addr=addr, name=name,
                product_name=product_name, product_type=product_type, **kwargs)
        logger.debug("[%s] - __init__ node uuid:%s", self.__class__.__name__, self.uuid)
        self.telemetry = None
        self.telemetry_ttl = 60
        self._telemetry_last = False
        self._telemetry_next_run = datetime.now() + timedelta(seconds=15)
        self._lock = threading.Lock()
        self._battery = -1.0
        self._battery_left = -1
        self._battery_charge = -1
        self._status = "NONE"
        self._cycle = "NONE"
        self._phase = "NONE"

        uuid = "status"
        self.values[uuid] = self.value_factory['sensor_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The status of the roomba',
            label='Status',
            get_data_cb=self.get_status,
        )
        poll_value = self.values[uuid].create_poll_value(default=90)
        self.values[poll_value.uuid] = poll_value

        uuid = "cycle"
        self.values[uuid] = self.value_factory['sensor_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The current cycle',
            label='Cycle',
            get_data_cb=self.get_cycle,
        )
        poll_value = self.values[uuid].create_poll_value(default=90)
        self.values[poll_value.uuid] = poll_value

        uuid = "phase"
        self.values[uuid] = self.value_factory['sensor_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The current phase',
            label='Phase',
            get_data_cb=self.get_phase,
        )
        poll_value = self.values[uuid].create_poll_value(default=90)
        self.values[poll_value.uuid] = poll_value

        uuid = "battery_left"
        self.values[uuid] = self.value_factory['sensor_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The time left on battery',
            label='Expire',
            get_data_cb=self.get_battery_left,
        )
        poll_value = self.values[uuid].create_poll_value(default=300)
        self.values[poll_value.uuid] = poll_value

        uuid = "battery_charge"
        self.values[uuid] = self.value_factory['sensor_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The time left for charging battery',
            label='Charging',
            get_data_cb=self.get_battery_charge,
        )
        poll_value = self.values[uuid].create_poll_value(default=300)
        self.values[poll_value.uuid] = poll_value

        uuid = "battery_percent"
        self.values[uuid] = self.value_factory['sensor_percent'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The percent charge of the battery',
            label='Percent',
            get_data_cb=self.get_battery_percent,
        )
        poll_value = self.values[uuid].create_poll_value(default=60)
        self.values[poll_value.uuid] = poll_value

        uuid = "ip_ping"
        self.values[uuid] = self.value_factory['ip_ping'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='Ping the vacuum',
            label='Ping',
        )
        config_value = self.values[uuid].create_config_value(help='The IP of the vacuum', label='IP',)
        self.values[config_value.uuid] = config_value
        poll_value = self.values[uuid].create_poll_value(default=300)
        self.values[poll_value.uuid] = poll_value

        uuid = "blid"
        self.values[uuid] = self.value_factory['config_string'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='blid to connect the irobot cloud',
            label='blid',
        )

        uuid = "robotpwd"
        self.values[uuid] = self.value_factory['config_password'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='robotpwd to connect the roomba',
            label='robotpwd',
        )

        uuid = "buttons"
        self.values[uuid] = self.value_factory['action_list'](options=self.options, uuid=uuid,
            node_uuid=self.uuid,
            help='The buttons on the roomba',
            label='Buttons',
            list_items=['clean', 'spot', 'dock', 'quick', 'stop', 'start', 'pause', 'resume', 'wake', 'reset', 'find' ],
            set_data_cb=self.set_button,
            is_writeonly = True,
            cmd_class = COMMAND_ROOMBA_VACUUM,
        )

    def get_telemetry(self):
        """Roomba method which fetches telemetry data about the robot.
        {
            "status": "OK",
            "method": "getStatus",
            "sku": "",
            "country": "",
            "postalCode": "",
            "regDate": "2016-06-23",
            "hardwareVersion": "",
            "manualUpdate": 0.0,
            "swUpdateAvailable": "",
            "schedHold": 0.0,
            "autoEvacCount": "",
            "autoEvacFlags": "",
            "wifiDiagnostics": "",
            "autoEvacModel": "",
            "milestones": "",
            "robotName": "Roomba",
            "robotLanguage": 1.0,
            "tzName": "Europe/Paris",
            "twoPass": 0.0,
            "noAutoPasses": "",
            "openOnly": 0.0,
            "carpetBoost": 0.0,
            "binPause": 1.0,
            "vacHigh": 0.0,
            "noPP": 0.0,
            "ecoCharge": 0.0,
            "mission": "{\"nMssn\":8,\"done\":\"cncl\",\"flags\":32,\"sqft\":0,\"runM\":0,\"chrgM\":0,\"pauseM\":1,\"doneM\":0,\"dirt\":0,\"chrgs\":0,\"saves\":0,\"evacs\":0,\"pauseId\":0,\"wlBars\":[0,0,0,0,0]}",
            "preventativeMaintenance": "[{\"partId\":\"bin\",\"date\":\"2016-06-23\",\"distance\":55,\"runtime\":0,\"months\":0,\"notified\":false},{\"partId\":\"core\",\"date\":\"2016-06-23\",\"distance\":55,\"runtime\":0,\"months\":0,\"notified\":false},{\"partId\":\"extractor\",\"date\":\"2016-06-23\",\"distance\":55,\"runtime\":0,\"months\":0,\"notified\":false}]",
            "cleanSchedule": "{\"cycle\":[\"none\",\"none\",\"none\",\"none\",\"none\",\"none\",\"none\"],\"h\":[0,0,0,0,0,0,0],\"m\":[0,0,0,0,0,0,0]}",
            "robot_status": "{\"flags\":8,\"cycle\":\"quick\",\"phase\":\"run\",\"pos\":{\"theta\":0,\"point\":{\"x\":0,\"y\":0}},\"batPct\":97,\"expireM\":0,\"rechrgM\":0,\"error\":0,\"notReady\":0,\"mssnM\":0,\"sqft\":0}",
            "softwareVersion": "v1.2.9",
            "lastSwUpdate": "2016-06-23 17:55:55+0000",
            "engBuild": "",
            "bbrun": "{\"hr\":0,\"min\":8,\"sqft\":0,\"nStuck\":0,\"nScrubs\":0,\"nPicks\":23,\"nPanics\":0,\"nCliffsF\":24,\"nCliffsR\":34,\"nMBStll\":0,\"nWStll\":0,\"nCBump\":0}",
            "missing": false,
            "ota": "{\"st\":0,\"err\":0,\"lbl\":\"\"}"
        }

        """
        if self._telemetry_next_run < datetime.now():
            locked = self._lock.acquire(False)
            if locked == True:
                try:
                    self._telemetry = self.command('getStatus')
                    logger.debug("[%s] - self._telemetry %s", self.__class__.__name__, self._telemetry)
                    self._status = self._telemetry['status']
                    self._telemetry['robot_status'] = json_loads(self._telemetry['robot_status'])
                    self._battery = self._telemetry['robot_status']['batPct']
                    self._battery_left = self._telemetry['robot_status']['expireM']
                    self._battery_charge = self._telemetry['robot_status']['rechrgM']
                    self._cycle = self._telemetry['robot_status']['cycle']
                    self._phase = self._telemetry['robot_status']['phase']
                    self._telemetry_last = True
                except Exception:
                    logger.exception("[%s] - Exception in get_telemetry", self.__class__.__name__)
                    self._telemetry_last = False
                finally:
                    self._lock.release()
                secs = self.values['ip_ping_poll'].data
                if secs < 0:
                    secs=60
                self._telemetry_next_run = datetime.now() + timedelta(seconds=secs)

    def check_heartbeat(self):
        """Check that the component is 'available'
        """
        return self._telemetry_last

    def get_cycle(self, node_uuid, index):
        """Return the current cycle
        """
        self.get_telemetry()
        return self._cycle

    def get_phase(self, node_uuid, index):
        """Return the current phase
        """
        self.get_telemetry()
        return self._phase

    def get_battery_percent(self, node_uuid, index):
        """Return the battery charge
        """
        self.get_telemetry()
        return self._battery

    def get_battery_left(self, node_uuid, index):
        """Return the battery charge
        """
        self.get_telemetry()
        return self._battery_left

    def get_battery_charge(self, node_uuid, index):
        """Return the battery charge
        """
        self.get_telemetry()
        return self._battery_charge

    def get_status(self, node_uuid, index):
        """Return the dock state
        """
        self.get_telemetry()
        return self._status

    def set_button(self, node_uuid, index, data):
        """Return the dock state
        """
        if data == "clean":
            self.command('multipleFieldSet', 'clean')
        elif data == "spot":
            self.command('multipleFieldSet', 'spot')
        elif data == "dock":
            self.command('multipleFieldSet', 'dock')
        elif data == "quick":
            self.command('multipleFieldSet', 'quick')
        elif data == "stop":
            self.command('multipleFieldSet', 'stop')
        elif data == "start":
            self.command('multipleFieldSet', 'start')
        elif data == "pause":
            self.command('multipleFieldSet', 'pause')
        elif data == "resume":
            self.command('multipleFieldSet', 'resume')
        elif data == "wake":
            self.command('multipleFieldSet', 'wake')
        elif data == "reset":
            self.command('multipleFieldSet', 'reset')
        elif data == "find":
            self.command('multipleFieldSet', 'find')
        else:
            logger.warning("[%s] - set_button unknown data %s", self.__class__.__name__, data)

    def command(self, command, value=None, args=None):
        """Send command to the roomba 900
        """
        logger.debug("[%s] - Start processing command %s", self.__class__.__name__, command)
        try:
            params = {
                "blid":self.values['blid'].data,
                "robotpwd":self.values['robotpwd'].data,
                "command":command,
                "value":value,
            }
            uri = 'https://irobot.axeda.com/services/v1/rest/Scripto/execute/AspenApiRequest?blid={blid}&robotpwd={robotpwd}&method={command}'
            if value is not None:
                uri += '&value=%7B%0A%20%20%22remoteCommand%22%20:%20%22{value}%22%0A%7D';
            r = requests.get(uri.format(**params))
            ret = json_loads(r.text)
            return ret
        except Exception:
            logger.error("[%s] - Command %s failed", self.__class__.__name__, command)
