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
import logging


class DAL:

    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger("SCHEDULER")

    # EXPERIMENTS

    def get_experiment(self, experiment_id):
        return self.db.get_document(
            doc_query={'_id': experiment_id},
            coll_name='experiments')

    def get_experiment_state(self, experiment_id):
        """ """
        return str(self.get_experiment(experiment_id)['state'])

    def retrieve_experiment_from_queue(self):
        return self.db.pop_document({}, 'queue', 'queue')

    def retrieve_experiment_from_running_queue(self):
        return self.db.pop_document({}, 'running', 'running')

    def update_experiment_state(self, experiment_id, new_state):
        self.db.update_document(
            doc_query={'_id': experiment_id},
            doc_update={'state': new_state},
            coll_name='experiments')

    def update_running_experiment_state(self, experiment_id, new_state):
        self.db.update_document(
            doc_query={'_id': experiment_id},
            doc_update={'state': new_state},
            coll_name='running')

    def update_experiment_launch_time(self, experiment_id, launch_time):
        self.db.update_document(
            doc_query={'_id': experiment_id},
            doc_update={'launch_time': launch_time},
            coll_name='experiments')

    def send_experiment_to_queue(self, experiment_id):
        self.db.push_document(
            doc_query={}, key='queue', element=experiment_id,
            coll_name='queue')

    def delete_experiment_from_running_queue(self, experiment_id):
        self.db.pull_document(
            doc_query={}, key='running',
            element={'experiment_id': experiment_id}, coll_name='running')

    # PROJECTS

    def get_project(self, project_id):
        return self.db.get_document({"_id": project_id}, "projects")

    # MODELS

    def get_model(self, template_name):
        return self.db.get_document({'filename': template_name}, "models")

    # METRICS

    def get_accuracy(self, experiment_id):
        """Return the accuracy for the experiment."""
        metrics = self.db.get_document({'name': str(experiment_id) + '-metrics'}, 'experimentsMetrics')
        accuracy = 0
        try:
            accuracy = metrics['metrics'].pop()['accuracy']
        except Exception:
            self.logger.info('No metrics yet')
        return accuracy

    def get_experiment_time(self, experiment_id):
        """Return the experiment's execution time."""
        metrics = self.db.get_document(
            {'name': str(experiment_id) + '-metrics'}, 'experimentsMetrics')
        try:
            experiment_time = metrics['metrics'].pop()['experiment_time']
        except Exception:
            self.logger.debug('No metrics yet')
            experiment_time = 0
        return experiment_time

    def save_experiment_result(self, project_id, experiment_id, accuracy):
        """Save the result for the experiment in order to categorize the best."""
        result_id = self.db.save_document({
            'project_id': project_id,
            'experiment_id': experiment_id,
            'accuracy': accuracy,
            'isBest': False,
            'experiment_time': self.get_experiment_time(experiment_id)}, "results")
        self.logger.info("Results saved! Document id: " + str(result_id))

    # SYSTEM

    def get_system_parameters(self):
        parameters = self.db.get_document({}, 'system')
        return parameters

    def get_running_experiments(self):
        return self.db.get_document(doc_query={}, coll_name='running')

    def save_running_experiment(self, experiment):
        self.db.push_document(
            doc_query={}, key='running',
            element={
                'experiment_id': experiment['_id'],
                'launch_time': experiment['launch_time'],
                'name': experiment['name']},
            coll_name='running')
