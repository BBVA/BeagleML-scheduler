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
projects_api = Blueprint('projects_api', __name__)


@projects_api.route('/api/v1/projects', methods=['GET'])
def get_projects():
    """
    Get a list of uploadad projects.
    Example request::
        GET /projects
    """
    api_control = current_app.config['API_CONTROL']
    serializer = current_app.config['SERIALIZER']

    projects = api_control.get_projects()
    return serializer.jsonify(projects)


@projects_api.route('/api/v1/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Get a project based on its ID.
    Example request::
        GET /projects/6890192d8b6c40e5af16f13aa036c7dc
    """
    # NOTE: links{ cada experimento}
    # NOTE: actions{ deleteExperiments, delte_project}
    # NOTE: info{ parametros del proyecto}
    api_control = current_app.config['API_CONTROL']
    serializer = current_app.config['SERIALIZER']

    project = api_control.get_project(project_id)
    project["id"] = project["_id"]
    project.pop('_id', None)

    logger.debug(project)
    return serializer.jsonify(project)


@projects_api.route('/api/v1/projects/<project_id>/experiments', methods=['GET'])
def get_experiments_project(project_id):
    """
    Get the experiments (paginated) of a project based on the project ID.
    Example request::
        GET /projects/6890192d8b6c40e5af16f13aa036c7dc/experiments
    """
    api_control = current_app.config['API_CONTROL']
    serializer = current_app.config['SERIALIZER']

    limit = int(request.args.get('limit', 10, type=int))
    offset = int(request.args.get('offset', 0, type=int))
    response = dict()
    response['info'] = {}
    response['info']['limit'] = limit
    response['info']['offset'] = offset
    response['info']['experiments'], response['info']['total'] = api_control.get_experiments_project(
        project_id, limit, offset)
    return serializer.jsonify(response)


@projects_api.route('/api/v1/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Delete a project and all its experiments.
    Example request::
        DEL /api/v1/projects/6890192d8b6c40e5af16f13aa036c7dc
    """
    api_control = current_app.config['API_CONTROL']
    api_control.delete_project_experiments(project_id)
    api_control.delete_project(project_id)
    return make_response('', 204)


@projects_api.route('/api/v1/projects', methods=['POST'])
def add_project():
    """
    Upload a project definition, and save its experiments to BBDD.
    """
    project = request.get_json()
    model_id = project["model_id"]
    project_id = save_project(project, model_id)

    # Launch Heuristic
    heuristic = project['optimization']
    error = launch_heuristic(heuristic, project_id, model_id)
    if error:
        return make_response(error, 400)

    return make_response('Experiment definition uploaded!!', 200)


def save_project(project, model_id):
    """Save project and experiments in BBDD from the project definition."""
    api_control = current_app.config['API_CONTROL']

    document = dict()
    document['name'] = project['name']
    document['model_id'] = model_id
    document['time_out'] = project["experiment_timeout"]
    document['accuracy_limit'] = project["experiment_accuracy_limit"]
    document['experiments'] = list()
    document['optimization'] = project['optimization']
    document['type'] = project['optimization']['type']
    document['parameters'] = project['parameters']
    document['template'] = project['template']

    logger.info('Configuring project ' + document['name'])
    project_id = api_control.save_project(document)
    logger.info('Project saved!!')

    api_control.update_last_state(document)

    return project_id


def launch_heuristic(heuristic, project_id, model_id):
    error = ""
    if heuristic['type'] == "grid":
        logger.info('Launching %s heuristic for project %s', heuristic['type'], project_id)
        app.send_task("grid_search", args=(str(project_id), str(model_id)))
    elif heuristic['type'] == "random":
        logger.info('Launching %s heuristic for project %s', heuristic['type'], project_id)
        app.send_task("random_search", args=(str(project_id), str(model_id), heuristic['total_n_experiments']))
    elif heuristic['type'] == "double_deep_qlearning":
        logger.info('Launching %s heuristic for project %s', heuristic['type'], project_id)
        app.send_task("double_deep_qlearning", args=(str(project_id), str(model_id), heuristic['total_n_episodes']))
    elif heuristic['type'] == "deep_qlearning":
        logger.info('Launching %s heuristic for project %s', heuristic['type'], project_id)
        app.send_task("deep_qlearning", args=(str(project_id), str(model_id), heuristic['total_n_episodes']))
    else:
        error = "Heuristic type not supported!"
        logger.error('Heuristic type - %s - not supported!', heuristic['type'])
    return error
