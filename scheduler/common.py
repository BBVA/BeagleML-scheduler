"""
Copyright 2018 Banco Bilbao Vizcaya Argentaria, S.A.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from celery import Celery

from scheduler.system.dbConnection import DBConnector

from scheduler.settings import *

logger = logging.getLogger("SCHEDULER")


def common_init():

    config = {x: y for x, y in globals().items() if not x.startswith("_")}

    # Initialize DB
    db = DBConnector(MONGODB_URL, MONGODB_PORT,
                     MONGODB_DATABASE, MONGODB_USER,
                     MONGODB_PASSWORD)
    config['DB'] = db

    return config

