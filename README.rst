conplyent
=========

Python-based distributed console executor. This library includes two main wrappers: console and client/server. Conplyent provides a wrapper around the subprocess library to execute commands on the console seemlessly without interruption on your main process. Conplyent also provides a wrapper around the ZMQ library to create a client/server connection which provides many shell features to control a remote executor. Conplyent is primarily built to simplify access to Systems Under Test.

Installation
============

.. code:: sh

    pip install conplyence

Requirements
============

Conplyent is currently only supported in Python 3.4.3+... Python2 support not planned in the near future.

PyZMQ -- https://github.com/zeromq/pyzmq

Click -- https://github.com/pallets/click

Documentation
=============

https://conplyent.readthedocs.io/en/latest/
