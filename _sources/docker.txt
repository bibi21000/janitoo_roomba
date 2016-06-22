==========================
Using the docker appliance
==========================

.. jnt-badge::
    :badges: docker


Installing Docker
=================

Install docker using the following documentation https://docs.docker.com/engine/installation/


Initial installation
====================

Create a 'store' container  :

.. code:: bash

    $ make docker-local-store

Create a 'running' container :

.. code:: bash

    $ make docker-local-running

Yous should now have 2 created containers :

.. code:: bash

    $ docker ps -a

.. code:: bash

    CONTAINER ID        IMAGE                          COMMAND             CREATED             STATUS      PORTS       NAMES
    a6459f44a4d9        bibi21000/janitoo_roomba   "/root/auto.sh"     29 seconds ago      Created                 roomba_running
    02479e7eeea1        bibi21000/janitoo_roomba   "/bin/true"         42 seconds ago      Created                 roomba_store


Start the container
===================

Start it :

.. code:: bash

    $ docker start roomba_running

Check that is running :

.. code:: bash

    $ docker ps

.. code:: bash

    CONTAINER ID        IMAGE                          COMMAND             CREATED             STATUS              PORTS                  NAMES
    a6459f44a4d9        bibi21000/janitoo_roomba       "/root/auto.sh"     30 seconds ago      Up 6 seconds        0.0.0.0:8882->22/tcp   roomba_running

And stop it :

.. code:: bash

    $ docker stop roomba_running


Customize your installation
===========================

You can find basis customizations tips here : https://bibi21000.github.io/janitoo_docker_appliance/customize.html.

This configuration is saved in the 'store' container.

Configuration
-------------

Update the roomba configuration file :

.. code:: bash

    $ ssh root@127.0.0.1 -p 8882

Default password is janitoo. You can change it but it will be restored on the next running container update. Prefer the key solutions.

Open the configuration file. The docker image contains a nano or vim for editing files :

.. code:: bash

    root@8eafc45f6d09:~# vim /opt/janitoo/etc/janitoo_roomba.conf

You must at least update the broker ip. It should match the ip address of your shared "mosquitto" :

.. code:: bash

    broker_ip = 192.168.1.14

If you plan to install more than one janitoo_roomba image on your network, you must change the hadd of the bus and components :

.. code:: bash

    hadd = 0051/0000

to

.. code:: bash

    hadd = 0052/0000

And so on for 0051/0001, ... Keep in mind that hadd must be unique on your network.

Save your updates and restart jnt_roomba :

.. code:: bash

    root@8eafc45f6d09:~# killall jnt_roomba

Vaccums
-------

Update the configuration according to your installation :

.. code:: bash

    [roomba__roomba1]
    heartbeat = 30
    name = Roomba 765
    location = Home
    hadd = 0051/0001
    ip_ping_config_0 = 192.168.14.64
    username_0 = admin
    password_0 = roombawifi

Querying
========

.. code:: bash

    $ jnt_query node --hadd 0051/0001 --vuuid request_info_users

.. code:: bash

    request_info_users
    ----------
    hadd       uuid                           idx  data                      units      type  genre cmdclass help
    0051/0001  ip_ping                        0    1                         None       1     2     48       Ping the vacuum
    0051/0001  temperature                    0    33.0                      °C         3     2     49       The temperature of the roomba
    0051/0001  battery_current                0    2918.0                    mA         3     2     49       The current of the battery
    0051/0001  current                        0    63.0                      mA         3     2     49       The dock current
    0051/0001  drive                          0    None                      None       5     2     8193     Drive the roomba to a position
    0051/0001  battery_capacity               0    2918.0                    mA         3     2     49       The capacity of the battery
    0051/0001  buttons                        0    None                      None       5     2     8192     The buttons on the roomba
    0051/0001  dock                           0    Trickle charging          None       8     2     49       The state of the roomba dock
    0051/0001  voltage                        0    16.61                     V          3     2     49       The dock voltage
    0051/0001  battery_charge                 0    100.0                     %          3     2     49       The charge of the battery

.. code:: bash

    $ jnt_query node --hadd 0051/0001 --vuuid request_info_configs

.. code:: bash

    request_info_configs
    ----------
    hadd       uuid                           idx  data                      units      type  genre cmdclass help
    0051/0000  location                       0    testroombalocation        None       8     3     112      The location of the node
    0051/0000  name                           0    testroombaname            None       8     3     112      The name of the node
    0051/0001  username                       0    admin                     None       8     3     112      Username to connect the roomba
    0051/0001  temperature_poll               0    60                        seconds    4     3     112      The poll delay of the value
    0051/0001  battery_current_poll           0    60                        seconds    4     3     112      The poll delay of the value
    0051/0001  name                           0    testroomba1name           None       8     3     112      The name of the node
    0051/0001  battery_charge_poll            0    60                        seconds    4     3     112      The poll delay of the value
    0051/0001  drive_config                   0    None                      None       2     3     112      A list of tuples (velocity, radius, time) from dock positions
    0051/0001  voltage_poll                   0    60                        seconds    4     3     112      The poll delay of the value
    0051/0001  location                       0    testroombalocation        None       8     3     112      The location of the node
    0051/0001  ip_ping_poll                   0    60                        seconds    4     3     112      The poll delay of the value
    0051/0001  battery_capacity_poll          0    60                        seconds    4     3     112      The poll delay of the value
    0051/0001  dock_poll                      0    60                        seconds    4     3     112      The poll delay of the value
    0051/0001  ip_ping_config                 0    192.168.14.64             None       33    3     112      The IP of the vacuum
    0051/0001  password                       0    roombawifi                None       20    3     112      Password to connect the roomba
    0051/0001  current_poll                   0    60                        seconds    4     3     112      The poll delay of the value


It's time to clean :

.. code:: bash

    $ jnt_query query --hadd 0051/0001 --uuid buttons --genre user --cmd_class 8192 --is_writeonly True --data clean

And go back to dock :

.. code:: bash

    $ jnt_query query --hadd 0051/0001 --uuid buttons --genre user --cmd_class 8192 --is_writeonly True --data clean
    $ jnt_query query --hadd 0051/0001 --uuid buttons --genre user --cmd_class 8192 --is_writeonly True --data dock

Performances
============

The top result in the running appliance :

.. code:: bash

    root@7de7e4993b13:~# top

.. code:: bash

    top - 18:10:48 up 17 days, 23:48,  1 user,  load average: 0.19, 0.29, 0.44
    Tasks:   8 total,   1 running,   7 sleeping,   0 stopped,   0 zombie
    %Cpu(s):  5.0 us,  1.4 sy,  0.0 ni, 93.1 id,  0.5 wa,  0.0 hi,  0.0 si,  0.0 st
    KiB Mem:  11661364 total,  9691100 used,  1970264 free,   786036 buffers
    KiB Swap: 19530748 total,   503648 used, 19027100 free.  2752660 cached Mem

      PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
       13 root      20   0  487452  24556   4368 S   0.6  0.2   1:38.65 /usr/local/bin/python /usr/local/bin/jnt_roomba -c /etc/janitoo/janitoo_roomba.conf front
      147 root      20   0   21932   1392   1016 R   0.6  0.0   0:00.01 top
        1 root      20   0   21732   1580   1312 S   0.0  0.0   0:00.03 /bin/bash /root/auto.sh
       10 root      20   0   55496  10052   1328 S   0.0  0.1   0:02.75 /usr/bin/python /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
       11 root      39  19   23492   1468   1176 S   0.0  0.0   0:04.63 top -b
       12 root      20   0   55160   3112   2444 S   0.0  0.0   0:00.02 /usr/sbin/sshd -D
      141 root      20   0   82696   3948   3100 S   0.0  0.0   0:00.05 sshd: root@pts/0
      143 root      20   0   20236   1880   1464 S   0.0  0.0   0:00.01 -bash

Administer your containers
==========================

You can find basis administration tips here : https://bibi21000.github.io/janitoo_docker_appliance/administer.html.
