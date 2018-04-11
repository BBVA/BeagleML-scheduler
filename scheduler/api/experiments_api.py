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
from flask import Blueprint
from flask import make_response, request, current_app

import logging

logger = logging.getLogger("SCHEDULER")

experiments_api = Blueprint('experiments_api', __name__)


@experiments_api.route('/api/v1/experiments/<experiment_id>', methods=['GET'])
def get_experiment(experiment_id):
    """Return the info and actions for a experiment."""

    api_control = current_app.config['API_CONTROL']
    serializer = current_app.config['SERIALIZER']

    experiment = api_control.get_experiment(experiment_id)

    logger.debug(experiment)

    data = dict({"links": {}, "actions": {}, "info": {}})
    data['info'] = experiment
    data['links']['metrics'] = '/metrics/' + str(experiment['_id'])

    # FIXME: delete experiment borra de todo, stop experiment borra del pool
    # Si existe el experimento y no se ha ejecutado deberia estar en la cola
    data['actions']['deleteExperiment'] = '/experiments/' + experiment_id
    data['actions']['deleteExperimentQueue'] = '/queue/' + experiment_id
    data['actions']['deleteExperimentPool'] = '/pool/' + experiment_id
    # TODO: Hacer que prioritize solo se pueda si esta en la cola
    if experiment['state'] is 'queue':
        data['actions']['prioritizeExperiment'] = (
            '/experiments/' + experiment_id + '/priority')
        data['actions']['unPrioritizeExperiment'] = (
            '/experiments/' + experiment_id + '/priority')
    elif experiment['state'] is 'pool':
        data['actions']['stop'] = '/experiments/' + experiment_id + '/stop'
    return serializer.jsonify(data)


@experiments_api.route('/api/v1/experiments/<experiment_id>/metrics', methods=['GET'])
def get_experiment_metrics(experiment_id):
    """Return the metrics for a experiment."""
    serializer = current_app.config['SERIALIZER']
    api_control = current_app.config['API_CONTROL']
    metrics = api_control.get_metrics(experiment_id)
    return serializer.jsonify(metrics)


@experiments_api.route('/api/v1/experiments/<experment_id>', methods=['DELETE'])
def delete_experiment(experiment_id):
    """Delete an experiment."""
    api_control = current_app.config['API_CONTROL']
    api_control.delete_experiment(experiment_id)
    return make_response('succeed', 200)
