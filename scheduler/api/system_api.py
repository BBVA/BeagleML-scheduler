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
from flask import Blueprint, current_app
from flask import make_response, request
from celery import Celery

import logging

logger = logging.getLogger("SCHEDULER")

app = Celery('scheduler')
app.config_from_object('scheduler.settings')
system_api = Blueprint('system_api', __name__)


@system_api.route('/api/v1/systems', methods=['GET'])
def get_systems():
    api_control = current_app.config['API_CONTROL']
    serializer = current_app.config['SERIALIZER']

    limit = int(request.args.get('limit', 10, type=int))
    offset = int(request.args.get('offset', 0, type=int))
    projects = api_control.get_projects()
    system_parameters = api_control.get_system_parameters()
    pools = api_control.get_pools(offset, limit)
    systems = api_control.get_systems()

    # TODO: until multisystem we use only 0-index
    systems[0]['projects'] = projects
    systems[0]['pools'] = pools
    systems[0]['running'] = system_parameters['running']
    if system_parameters['running']:
        systems[0]['state'] = "Launching experiments"
    else:
        systems[0]['state'] = "Waiting for launching"
    systems[0]['experimentsLimit'] = system_parameters['experiments_limit']

    return serializer.jsonify(systems)


@system_api.route('/api/v1/systems/<system_id>', methods=['PUT'])
def configure_system(system_id):
    """
    Change system parameters.

    experimentsLimit: maximum number of experiments executing at the same time.
    running: change the system from 'active state' to 'waiting for launching'
    """
    api_control = current_app.config['API_CONTROL']

    request_data = request.get_json()
    logger.info(request_data)

    parameters = dict()

    if 'running' in request_data:
        running = str(request_data['running']).lower() == 'true'
        parameters['running'] = running

    if 'experimentsLimit' in request_data:
        limit = int(request_data['experimentsLimit'])
        parameters['experiments_limit'] = limit

    if parameters:
        api_control.update_system_parameters(system_id, parameters)

    return make_response('succeed', 200)


@system_api.route('/api/v1/systems/<system_id>/reset', methods=['POST'])
def system_reset(system_id):
    """
    Delete all the experiments in the database.
    """
    api_control = current_app.config['API_CONTROL']

    api_control.delete_pool()
    api_control.system_reset(system_id)
    # Kill celery tasks
    app.control.purge()

    return make_response('succeed', 200)
