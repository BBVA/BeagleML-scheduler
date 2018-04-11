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

pools_api = Blueprint('pools_api', __name__)

@pools_api.route('/api/v1/pools', methods=['GET'])
def get_pools():
    """Muestra la lista de experimentos en running."""
    api_control = current_app.config['API_CONTROL']
    serializer = current_app.config['SERIALIZER']
    limit = int(request.args.get('limit', 10, type=int))
    offset = int(request.args.get('offset', 0, type=int))
    response = api_control.get_pools(offset, limit)

    return serializer.jsonify(response)

@pools_api.route('/api/v1/pools', methods=['DELETE'])
def delete_pool():
    """Delete all the experiemt from the pool."""
    # FIXME: funcionalidad de la api en el lanzador CHECK
    api_control = current_app.config['API_CONTROL']
    api_control.delete_pool()
    return make_response('succeed', 200)


@pools_api.route('/api/v1/pools/<experiment_id>', methods=['DELETE'])
def delete_experiment_from_pool(experiment_id):
    """Delete experiment in the pool."""
    api_control = current_app.config['API_CONTROL']
    api_control.delete_experiment_from_pool(experiment_id)
    return make_response('succeed', 200)
