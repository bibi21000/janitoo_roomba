# -*- coding: utf-8 -*-

"""The roomba server

See http://www.roowifi.com/sample-python-gtk/
See https://github.com/maxvitek/roowifi
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
#Globals
import logging
logger = logging.getLogger('janitoo.roomba')
import os
import traceback
#Specific
from pkg_resources import get_distribution, DistributionNotFound
#Janitoo
from janitoo.server import JNTServer

class RoombaServer(JNTServer):
    """The Roomba Server

    """
    def _get_egg_path(self):
        """Return the egg path of the module. Must be redefined in server class. Used to find alembic migration scripts.
        """
        try:
            return get_distribution('janitoo_roomba')
        except AttributeError:
            return os.path.join("/opt/janitoo/src", 'src-roomba/config')

