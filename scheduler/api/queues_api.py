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

import logging

logger = logging.getLogger("SCHEDULER")

queues_api = Blueprint('queues_api', __name__)


@queues_api.route('/api/v1/queues', methods=['GET'])
def get_queues():
    """Muestra la cola."""
    api_control = current_app.config['API_CONTROL']
    serializer = current_app.config['SERIALIZER']

    limit = int(request.args.get('limit', 10, type=int))
    offset = int(request.args.get('offset', 0, type=int))
    response = api_control.get_experiments_in_queues_paginated(offset, limit)

    return serializer.jsonify(response)


@queues_api.route('/api/v1/queues', methods=['DELETE'])
def delete_queue():
    """Delete all the experiments in the queue."""
    api_control = current_app.config['API_CONTROL']
    api_control.delete_queue()
    return make_response('succeed', 200)


@queues_api.route('/api/v1/queues/<experiment_id>', methods=['DELETE'])
def delete_experiment_from_queue(experiment_id):
    """Delete experiment in the queue."""
    api_control = current_app.config['API_CONTROL']
    api_control.delete_experiment_from_queue(experiment_id)
    return make_response('succeed', 200)
