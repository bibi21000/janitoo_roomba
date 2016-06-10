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

Pull the image :

.. code:: bash

    $ docker pull bibi21000/janitoo_roomba

Create a 'store' container  :

.. code:: bash

    $ docker create -v /root/.ssh/ -v /opt/janitoo/etc/ --name roomba_store bibi21000/janitoo_roomba /bin/true

Create a 'running' container :

.. code:: bash

    $ docker create --volumes-from roomba_store -p 8885:22 --name roomba_running bibi21000/janitoo_roomba

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
    a6459f44a4d9        bibi21000/janitoo_roomba       "/root/auto.sh"     30 seconds ago      Up 6 seconds        0.0.0.0:8885->22/tcp   roomba_running

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

    $ ssh root@127.0.0.1 -p 8885

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

Disks
-----

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

Performances
============

The top result in the running appliance :

.. code:: bash

    root@7de7e4993b13:~# top

.. code:: bash

    top - 19:08:40 up 10 days, 46 min,  1 user,  load average: 0.34, 0.50, 0.58
    Tasks:   8 total,   1 running,   7 sleeping,   0 stopped,   0 zombie
    %Cpu(s):  7.3 us,  3.9 sy,  0.0 ni, 88.5 id,  0.0 wa,  0.0 hi,  0.3 si,  0.0 st
    KiB Mem:  11661364 total, 11257872 used,   403492 free,   586084 buffers
    KiB Swap: 19530748 total,   301772 used, 19228976 free.  4392228 cached Mem

      PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND

Administer your containers
==========================

You can find basis administration tips here : https://bibi21000.github.io/janitoo_docker_appliance/administer.html.
