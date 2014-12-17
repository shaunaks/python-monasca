python-monasca
==================

python monasca implementation
=================================

To install the python api implementation, git clone the source and run the
following command::

    sudo python setup.py install

If it installs successfully, you will need to make changes to the following
two files to reflect your system settings, especially where kafka server is
located::

    /etc/monasca/monasca.ini
    /etc/monasca/monasca.conf

Once the configurations are modified to match your environment, you can start
up the server by following the following instructions.

To start the api server, run the following command:

    Running the server in foreground mode
    gunicorn -k eventlet --worker-connections=2000 --backlog=1000
             --paste /etc/monasca/monasca.ini

    Running the server as daemons
    gunicorn -k eventlet --worker-connections=2000 --backlog=1000
             --paste /etc/monasca/monasca.ini -D

To start a monasca micro service server, run the following command:

    monasca-service --config-file /etc/monasca/monasca-xxxx.conf

    where monasca-xxxx.conf should be a micro service specific
    configuration file. For example, to start the ElasticSearch persister
    micro service which read messages off of kafka queue and save the
    messages onto ElasticSearch, run the following command:

    monasca-service --config-file /etc/monasca/monasca-persister.conf


To start the monasca ui server, run the following command

    gunicorn -k eventlet --worker-connections=100 --backlogs=100
             --paste /etc/monasca/dashboard.conf

    the ElasticSearch Kibana has been changed. This section needs some
    rework.

To check if the code follows python coding style, run the following command
from the root directory of this project

    tox -e pep8

To run all the unit test cases, run the following command from the root
directory of this project

    tox -e py27   (or -e py26, -e py33)