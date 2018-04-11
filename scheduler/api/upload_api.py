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
import yaml
import json
import logging

from flask import Blueprint, current_app
from flask import make_response, request
from celery import Celery


logger = logging.getLogger("SCHEDULER")
app = Celery('scheduler')
app.config_from_object('scheduler.settings')

upload_api = Blueprint('upload_api', __name__)


@upload_api.route('/api/v1/upload', methods=['POST'])
def project_upload():
    if request.environ['HTTP_TYPE'] == 'model':
        response = upload_model_template(request)
    elif request.environ['HTTP_TYPE'] == 'project':
        response = upload_project_definition(request)
    else:
        return make_response('Type not supported or empty.', 400)

    return response


def upload_model_template(request):
    """
    Upload a model template, and save it to DDBB.
    """
    orch_name = current_app.config['ORCHESTRATOR']
    orch_url = current_app.config['ORCHESTRATOR_URL']
    orch_token = current_app.config['ORCHESTRATOR_TOKEN']

    serializer = current_app.config['SERIALIZER']

    filename, extension, file_in_string = check_uploaded_file(request)
    print("model_upload " + filename)

    error = app.send_task("orchestrator_extension_check",
                          args=(orch_url, orch_token, extension, orch_name)).get()
    if error:
        return make_response(error, 400)

    # Load model definition file
    if allowed_file(filename):
        logger.info('Model template %s received!', filename)

        if extension in ('yml', 'yaml'):
            template, error = load_yaml_file(file_in_string)
        else:  # JSON   
            template, error = load_json_file(file_in_string)

        if error:
            return make_response(error, 400)

    else:
        logger.error('Wrong file extension: %s', filename)
        return make_response('Wrong file extension', 400)

    logger.debug(template)
    template['filename'] = filename

    response = dict()
    response['template'] = template

    return serializer.jsonify(response)


def upload_project_definition(request):
    """
    Upload a project definition, and save its experiments to BBDD.
    """
    api_control = current_app.config['API_CONTROL']
    serializer = current_app.config['SERIALIZER']
    filename, extension, file_in_string = check_uploaded_file(request)

    # Load project definition file
    if allowed_file(filename) and extension in ('yml', 'yaml'):
        logger.info('Project definition file %s received!', filename)
        project, error = load_yaml_file(file_in_string)
        if error:
            return make_response(error, 400)
    else:
        logger.error('Wrong file extension: %s', filename)
        return make_response('Wrong file extension', 400)

    # TODO Check project syntax
    logger.info(project)

    # Check if the model has been uploaded previously
    model = api_control.get_model(project['template'])
    if model:
        logger.info('Model found: %s with id %s', project['template'], model['_id'])
        logger.info(model)
    else:
        return make_response('Error: project uploaded, but model' + model['_id'] + ' not found!!', 400)

    project['model_id'] = model['_id']

    return serializer.jsonify(project)


def load_yaml_file(file_in_string):
    """ """
    file_loaded, error = '', ''
    try:
        file_loaded = yaml.load(file_in_string)
    except yaml.YAMLError as exc:
        logger.error(exc)
        if hasattr(exc, 'problem_mark'):
            mark = exc.problem_mark
            error = "Bad file format. Check line " + str(mark.line + 1) + ", column " + str(mark.column + 1)
    return file_loaded, error


def load_json_file(file_in_string):
    """ """
    file_loaded, error = '', ''
    try:
        file_loaded = json.loads(file_in_string)
    except ValueError as error:  # TODO improve error handling
        logger.error("Error: ", error)
    return file_loaded, error


def allowed_file(filename):
    """
    Check if the file is allowed in the API.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def check_uploaded_file(api_request):
    """
    Perform some checks, and returns the filename and content of the uploaded file.
    """
    if not file_in_request(api_request):
        return make_response('No \'file\' part in POST request', 400)
    file_uploaded = api_request.files['file']
    if not has_filename(file_uploaded):
        return make_response('No file selected.', 400)

    file_in_bytes = file_uploaded.read()
    file_in_string = file_in_bytes.decode('utf8').replace("'", '"')
    filename = file_uploaded.filename
    extension = str(filename.split('.')[-1])

    return filename, extension, file_in_string


def file_in_request(api_request):
    """
    Check if the POST request has the file part.
    """
    if 'file' not in api_request.files:
        logger.error('No \'file\' part in POST request')
        return False
    else:
        return True


def has_filename(file_uploaded):
    """
    If the user does not select a file, the browser
    submits an empty part without filename.
    """
    if file_uploaded.filename == '':
        logger.error('No file selected.')
        return False
    else:
        return True
