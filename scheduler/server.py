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
# coding=utf-8
import traceback
import logging

from flask import Flask, request
from flask_cors import CORS

from scheduler.api.experiments_api import experiments_api
from scheduler.api.healthcheck_api import healthcheck_api
from scheduler.api.models_api import models_api
from scheduler.api.pools_api import pools_api
from scheduler.api.projects_api import projects_api
from scheduler.api.queues_api import queues_api
from scheduler.api.system_api import system_api
from scheduler.api.upload_api import upload_api

from scheduler.make_app import init
from scheduler.common import common_init

logger = logging.getLogger("SCHEDULER")

# Server
app = Flask(__name__)
app.config.from_pyfile('settings.py')
init(app, common_init())

CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(experiments_api)
app.register_blueprint(healthcheck_api)
app.register_blueprint(models_api)
app.register_blueprint(pools_api)
app.register_blueprint(projects_api)
app.register_blueprint(queues_api)
app.register_blueprint(system_api)
app.register_blueprint(upload_api)


# From https://gist.github.com/ivanlmj/dbf29670761cbaed4c5c787d9c9c006b
# and https://stackoverflow.com/questions/14037975/
# how-do-i-write-flasks-excellent-debug-log-message-to-a-file-in-production/39284642#39284642
@app.after_request
def after_request(response):
    # this if avoids the duplication of registry in the log,
    # since that 500 is already logged via @app.errorhandler
    if response.status_code != 500:
        logger.info('%s %s %s %s %s',
                    request.remote_addr,
                    request.method,
                    request.scheme,
                    request.full_path,
                    response.status)
    return response


@app.errorhandler(Exception)
def exceptions(e):
    tb = traceback.format_exc()
    logger.error('%s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                 request.remote_addr,
                 request.method,
                 request.scheme,
                 request.full_path,
                 tb)
    return "Internal Server Error", 500


def main():
    app.run(port=5000, host='127.0.0.1')


if __name__ == '__main__':
    main()
