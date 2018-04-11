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
"""Module for controling api functions interacting with the db."""
from bson.objectid import ObjectId
from ..settings import EXPERIMENT_STATES
import datetime

class ApiDAL:
    """This class is used to interact with the db."""

    def __init__(self, db):
        """
        Initializer.

        args:
            db: must be an object of dbConnection.
        """
        self.db = db

    # QUEUE
    def get_experiments_in_queue(self):
        """
        Return the list of experiments that are in the queue
        """
        queue = self.db.get_all_documents('queue')
        experiments = []
        if queue:
            experiments = queue[0]['queue']
        return experiments

    def get_experiments_in_queues_paginated(self, queue_shown, queue_shown_limit):
        """
        Return the execution queue in a list form.

        The method returns a tuple. The first element is a paginated list
        of the length specified in the parameters. The second element is the
        total number of experiments in the list.
        """
        end = queue_shown + queue_shown_limit
        queue = self.db.get_document_paginate_list(
            query={}, key='queue',
            coll_name='queue', end=end, start=queue_shown)
        if queue:
            experiments = []
            for _id in queue['queue']:
                experiments.append(self.get_experiment(_id))
            return experiments
        else:
            return []

    def delete_queue(self):
        """Delete all the experiments in the queue."""
        # TODO: delete experiments in the collections experiments,
        # project and metrics
        queue = self.db.get_document({}, 'queue')['queue']
        for experiment in queue:
            self.db.pull_document({}, 'queue', experiment, 'queue')

    def delete_experiment_from_queue(self, experiment_id):
        """Delete a experiment from the queue."""
        self.db.pull_document({}, 'queue', experiment_id, 'queue')

    # POOLS
    def get_pools(self, pool_shown, pool_shown_limit):
        """
        Return the execution queue in a list form.

        The method returns a tuple. The first element is a paginated list
        of the length specified in the parameters. The second element is the
        total number of experiments in the list.
        """
        end = pool_shown + pool_shown_limit
        pool = self.db.get_document_paginate_list(
            query={}, key='running',
            coll_name='running', end=end, start=pool_shown)
        total = self.db.count_array_document(
            query={}, key='running', coll_name='running')
        if pool:
            experiments = []
            for experiment in pool['running']:
                experiments.append(self.get_experiment(experiment['experiment_id']))
            return experiments
        else:
            return []

    def delete_pool(self):
        """
        Delete all the experiments in the pool.

        The experiments are stopped. The metrics collected to that time are
        deleted and the experiments return to the queue.
        """
        pool = self.db.get_document({}, 'running')['running']
        for experiment in pool:
            self.db.pull_document({}, 'running', experiment, 'running')
            self.db.update_document(
                doc_query={'_id': experiment['experiment_id']},
                doc_update={'state': "stopped"},
                coll_name='experiments')
            self.db.push_document(
                doc_query={}, key='queue', element=experiment['experiment_id'],
                coll_name='queue')
            self.db.delete_document(
                doc_query={'name': str(experiment['experiment_id'])
                           + '-metrics'},
                coll_name='experimentsMetrics')

    # MODELS
    def get_model(self, template):
        """Get the model data."""
        model = self.db.get_document(
            {'filename': template}, "models")
        return model

    def get_models(self):
        """Get all the models."""
        return self.db.get_all_documents("models")

    def save_model(self, template):
        """Save a single model."""
        template['create_time'] = datetime.datetime.utcnow()
        model_id = self.db.save_document(template, 'models')
        return model_id

    def update_model(self, template):
        """Update model's data."""
        template['create_time'] = datetime.datetime.utcnow()
        model = self.db.update_document({'filename': template['filename']}, template, 'models')
        return model

    # PROJECTS
    def get_project(self, project_id):
        """Get the project data."""
        project = self.db.get_document(
            {'_id': ObjectId(project_id)}, 'projects')
        project.update(self.get_num_state_experiments(ObjectId(project_id)))
        project.update(self.get_num_experiments(project))
        return project

    def save_project(self, project):
        """Save the project into BBDD."""
        project_id = self.db.save_document(
            {'name': project['name'],
             'create_time': datetime.datetime.utcnow(),
             'model_id': project['model_id'],
             'time_out': project['time_out'],
             'accuracy_limit': project['accuracy_limit'],
             'experiments': project['experiments'],
             'optimization': project['optimization'],
             'type': project['type'],
             'parameters': project['parameters'],
             'template': project['template']},
            'projects')
        return project_id

    def get_projects(self):
        """Return all the ids of the projects."""
        projects_ids = self.db.get_all_ids('projects')
        projects = []
        for project in projects_ids:
            project_data = dict()
            project_data['_id'] = project
            project_data['name'] = self.db.get_document(
                {'_id': ObjectId(project)}, 'projects')['name']
            project_data.update(self.get_num_state_experiments(project))

            projects.append(project_data)

        return projects

    def delete_project(self, project_id):
        """Delete a project."""
        self.db.delete_document({'_id': ObjectId(project_id)}, 'projects')

    # EXPERIMENTS
    def get_experiment(self, experiment_id):
        """Get the experiment data."""
        experiment = self.db.get_document(
            {'_id': ObjectId(experiment_id)}, 'experiments')
        return experiment

    def delete_experiment(self, experiment_id):
        """Delete a experiment and its metrics."""
        experiment = self.db.get_document(
            {'_id': ObjectId(experiment_id)}, 'experiments')
        if experiment:
            self.db.delete_document(
                {'_id': ObjectId(experiment_id)}, 'experiments')
            self.db.delete_document(
                {'name': experiment_id + '-metrics'}, 'metrics')

    def get_experiments_project(
            self, project_id, experiments_shown_limit, experiments_shown):
        """
        Return the experiments in a project paginated.

        The method returns a tuple. The first element is a paginated list
        of the length specified in the parameters. The second element is the
        total number of experiments in the list
        """
        end = experiments_shown + experiments_shown_limit
        query = {'_id': ObjectId(project_id)}
        project_paginated = self.db.get_document_paginate_list(
            query=query, key='experiments', coll_name='projects',
            end=end, start=experiments_shown)
        total = self.db.count_array_document(
            query=query, key='experiments', coll_name='projects')
        experiments = []
        for _id in project_paginated['experiments']:
            experiments.append(self.get_experiment(_id))
        return experiments, total

    def get_best_experiment(self, project_id):
        experiment_id = self.db.get_document({'project_id': ObjectId(project_id),
                                              'isBest': True}, "results")["experiment_id"]
        experiment = self.db.get_document({'_id': experiment_id}, "experiments")
        return experiment

    def delete_project_experiments(self, project_id):
        """
        Delete all the experiments associated with a project.
        First delete from experiments collection. Then from queue collection.
        """
        experiment_id = self.db.pop_document(
            {'_id': ObjectId(project_id)}, 'experiments', 'projects')
        while experiment_id:
            self.db.delete_document({'_id': ObjectId(experiment_id)}, 'experiments')
            self.db.pull_document({}, 'queue', experiment_id, 'queue')
            experiment_id = self.db.pop_document(
                {'_id': ObjectId(project_id)}, 'experiments', 'projects')

    def delete_experiment_from_pool(self, experiment_id):
        """Delete a experiment from the pool."""
        self.db.pull_document({}, 'running', experiment_id, 'running')

    # METRICS
    def get_metrics(self, experiment_id):
        """Return the metrics for one experiment."""
        metrics = self.db.get_document(
            {'name': experiment_id + '-metrics'}, 'experimentsMetrics')
        if metrics:
            return metrics['metrics']
        else:
            return 'No metrics yet'

    # SYSTEM
    def get_systems(self):
        """Get all the systems. Currently only 1."""
        return self.db.get_all_documents("system")

    def get_system_parameters(self):
        parameters = self.db.get_document({}, 'system')
        return parameters

    def update_system_parameters(self, system_id, parameters):
        error = self.db.update_document({'_id': ObjectId(system_id)}, parameters, 'system')
        if not parameters.get('running'):
            self.delete_pool()
        return error

    def system_reset(self, system_id):
        """
        Delete all the projects, experiments, queue and pool.

        system_id not used, but it would be useful to have +1 system.
        """
        self.db.delete_all_documents('projects')
        self.db.delete_all_documents('experiments')
        self.db.delete_all_documents('experimentsMetrics')
        self.delete_queue()
        self.delete_pool()

    def get_num_state_experiments(self, project_id):
        """
        Given a project, it returns a dictionary with the experiment states as
        keys, and the number of experiments in each state as values.
        """
        num_experiments = {}
        for state in EXPERIMENT_STATES:
            num_experiments[state] = self.db.get_number_documents(
                coll_name='experiments',
                query={'project_id': project_id, 'state': state})

        return num_experiments

    def get_num_experiments(self, project):
        """
        Get the number of experiments for a project.

        Return a dict with the key experiments and just the number
        of experiments.
        """
        experiments_in_project = dict(
            experiments=len(project['experiments']))
        return experiments_in_project

    # LAST STATE
    def update_last_state(self, project_definition):
        self.db.update_document(
            doc_query={'name': '_lastState'},
            doc_update=project_definition,
            coll_name='_lastState')