Monasca
=======

Monasca is a monitoring software allowing you to collect data from any compute
systems.

Install Prerequisite
====================

Monasca python implementation install process installs Monasca and most of its
dependencies automatically. However some components cannot be installed automatically
by python setup tools, they will have to be installed manually. These components are
python setup tools, python-dev, gunicorn and python-pip. Follow the steps below to
install dependencies::

To install setuptools, please reference to this page.

    https://pypi.python.org/pypi/setuptools

The typical process of installing setuptools is to download the tar.gz file
then tar -xvf and run python setup.py install

To install python-dev and pip, run the following command:

    sudo apt-get install python-dev python-pip

To install gunicorn, run the following command:

    sudo pip install gunicorn==19.1.0
    
Monasca depends on Kafka and ElasticSearch, both requires Java. If you do not
already have Java, Kafka and ElasticSearch server running, you will have to install
these servers. Please refer to respective document on how to install Java, Kafka and
ElasticSearch::

    http://www.java.com
    http://kafka.apache.org/documentation.html#introduction
    https://www.elastic.co/products/elasticsearch

Install Monasca
===============
Get the source code::

    git clone https://github.com/litong01/python-monasca.git

Run the python setup to install::

    sudo python setup.py install

If Monasca installs successfully, you can then make changes to the following
two files to reflect your system settings, such as Kafka server locations::

    /etc/monasca/monasca.ini
    /etc/monasca/monasca.conf

Once the configurations are modified to match your environment, you can start
up various services by following these instructions.

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

In the future, there might be other services such as threshold engine,
anomaly detection, alarms etc. All these services should be able to take
a specific configuration file to be launched. Here are the examples:

    monasca-service --config-file /etc/monasca/monasca-alarms.conf
    monasca-service --config-file /etc/monasca/monasca-anomaly.conf
    monasca-service --config-file /etc/monasca/monasca-threshold.conf

To start the monasca ui server, run the following command

    gunicorn -k eventlet --worker-connections=100 --backlogs=100
             --paste /etc/monasca/dashboard.conf

    the ElasticSearch Kibana has been changed. This section needs some
    rework.


Monasca Development
===================
To check if the code follows python coding style, run the following command
from the root directory of this project

    tox -e pep8

To run all the unit test cases, run the following command from the root
directory of this project

    tox -e py27   (or -e py26, -e py33)

To see the unit test case coverage, run the following command from the root
directory of the project

    tox -e cover

    If the command runs successfully, then set of files will be
    created in the root directory named cover. Open up the index.html
    from a browser to see the summary of the unit test coverage and
    the details.