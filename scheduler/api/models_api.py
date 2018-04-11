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
import logging, pdb

from flask import Blueprint, current_app
from flask import make_response, request

logger = logging.getLogger("SCHEDULER")

models_api = Blueprint('models_api', __name__)


@models_api.route('/api/v1/models', methods=['GET'])
def get_models():
    api_control = current_app.config['API_CONTROL']
    serializer = current_app.config['SERIALIZER']

    return serializer.jsonify(api_control.get_models())


@models_api.route('/api/v1/models/<model_id>', methods=['GET'])
def get_model(model_id):
    api_control = current_app.config['API_CONTROL']

    return api_control.get_model(model_id)


@models_api.route('/api/v1/models', methods=['POST'])
def add_model():
    body = request.get_json()
    model_id, error = save_model_template(body)

    if not error:
        logger.info('Model template %s stored with id %s', body['filename'], model_id)
        return make_response('Model template uploaded!', 200)
    else:
        return make_response('ERROR saving model template to BBDD.', 400)


def save_model_template(template):
    """
    Save model in BBDD from model template file.
    Input: dict
    Output: DDBB insert return value
    """
    api_control = current_app.config['API_CONTROL']

    logger.info('Saving model template in BBDD.')
    exists_model_template = api_control.get_model(template['filename'])
    model_document_id = ''
    if not exists_model_template:
        model_document_id = api_control.save_model(template)
    else:
        updated = api_control.update_model(template)
        if updated:
            model_document_id = exists_model_template['_id']
        logger.info('model ' + str(model_document_id))
    return (model_document_id, '') if model_document_id else ('', 'Error')
