#!/bin/bash

gunicorn --bind=0.0.0.0:5000 --worker-class gevent --workers 1 scheduler.server:app