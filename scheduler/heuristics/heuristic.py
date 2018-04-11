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
"""
Base class for Heuristics

Every heuristic must extend Heuristic class
"""
from scheduler.settings import *

from bson.objectid import ObjectId
from celery import Celery

app = Celery('scheduler')
app.config_from_object('scheduler.settings')


class Heuristic:
    """
    Heuristic interface
    Heuristics are responsible for ...

    :param project_id:    Project belonged to Heuristic
    :param model_id:      Model belonged to Heuristic
    """

    def __init__(self, project_id, model_id, **kwargs):
        self.db = kwargs.get("db")

        self.project_id = project_id
        self.model_id = model_id

        self.project = dict()
        self.model = dict()

    def check_heuristic_syntax(self):
        """
        Check the heuristic section of the project definition.
        """
        raise NotImplementedError("Heuristics should implement this!")

    def generate_experiments(self):
        """
        Every heuristic needs a pool of experiments to be executed.
        """
        raise NotImplementedError("Heuristics should implement this!")

    def evaluate(self):
        """

        :return:
        """
        raise NotImplementedError("Heuristics should implement this!")

    def run(self):
        """

        :return:
        """
        raise NotImplementedError("Heuristics should implement this!")

    def get_project_definition(self):
        """
        Every heuristic object controls a single project, that has been
        uploaded previously to the system.
        """
        self.project = self.db.get_document({'_id': ObjectId(self.project_id)}, "projects")

    def get_model_template(self):
        """
        Looks for the specified model template in BBDD.
        Later, calls orchestrator to parse the model template. Different orchestrators have different template
        formats. Ex: dcos - json; docker-compose - yaml.
        :return:
        """
        model = self.db.get_document({'_id': ObjectId(self.model_id)}, "models")
        model['_id'] = str(model['_id'])    # serialize bson object for celery task.
        model_parsed = app.send_task("parse_environment_variables",
                                     args=(ORCHESTRATOR_URL, ORCHESTRATOR_TOKEN,
                                           model, ORCHESTRATOR)).get(disable_sync_subtasks=False)
        self.model = model_parsed

    def send_experiments_to_queue(self, experiments_set):
        """
        Controls which experiments are sent to system queue.
        """
        experiments_ids = list()
        for experiment in experiments_set:

            experiment['state'] = 'queue'
            id_experiment = self.db.save_document(experiment, coll_name='experiments')

            self.db.update_document(
                doc_query={'_id': id_experiment, 'parameters.name': 'ROOT_TOPIC'},
                doc_update={'parameters.$.value': str(id_experiment)},
                coll_name='experiments')
            self.db.update_document(
                doc_query={'_id': id_experiment, 'parameters.name': 'METRICS_TOPIC'},
                doc_update={'parameters.$.value': str(id_experiment) + '-metrics'},
                coll_name='experiments')
            self.db.push_document(
                doc_query={}, key='queue', element=id_experiment,
                coll_name='queue')
            self.db.push_document(
                doc_query={'name': self.project['name']}, key='experiments',
                element=id_experiment, coll_name='projects')

            experiments_ids.append(id_experiment)

        return experiments_ids
