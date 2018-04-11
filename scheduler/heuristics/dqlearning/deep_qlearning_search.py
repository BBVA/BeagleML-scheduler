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
import datetime
import time
import numpy as np
import logging

from ..heuristic import Heuristic
from .rl_heuristic_agent import Agent
from scheduler.system.dbConnection import DBConnector
from bson.objectid import ObjectId
from scheduler.settings import *
from celery import task


class DQLearning(Heuristic):
    def __init__(self, project_id, model_id, total_n_episodes, **kwargs):
        self.logger = logging.getLogger("SCHEDULER")
        self.db = kwargs["db"]
        self.project_id = project_id
        self.model_id = model_id

        self.project = dict()
        self.model = dict()
        self.running_experiments = list()
        self.experiments_counter = 0

        super(DQLearning, self).get_project_definition()
        super(DQLearning, self).get_model_template()

        self.total_time_consumed = 0
        self.total_reward = 0
        self.executed_experiments_counter = 0
        self.episodes_counter = 0

        self.total_n_episodes = total_n_episodes
        self.experiments_failed_counter = 0

        self.state = np.array([self.total_time_consumed, self.total_reward, self.executed_experiments_counter]).reshape(
            1, 3)
        self.last_action = None

        self.last_reward = 0

        # TODO: Change to be flexible
        self.last_parameter_executed = 0.1

    def run(self):
        """
        Launch the full heuristic search process.
        :return: void
        """
        self.logger.info('Starting Reinforcement Search Heuristic...')
        agent = Agent()
        self.check_heuristic_syntax()
        self.init_queue(agent)

        while self.episodes_counter < self.total_n_episodes:
            self.logger.info('Evaluating...')
            time.sleep(3)
            self.evaluate(agent)

    def init_queue(self, agent):
        """
        Initialize the queue following the heuristic rules.
        :return: list
        """
        self.logger.info('Generating Initial Experiment...')
        action = self.run_reinforcement(agent)
        self.generate_experiments(action)
        self.last_action = action

    def evaluate(self, agent):
        """
        Manage the heuristic process until the search is finished.
        :return: void
        """
        for experiment_id in self.running_experiments:
            status_completed = self.check_completed(experiment_id)
            self.logger.info('Evaluating experiment: %s, %s', experiment_id, status_completed)

            if status_completed:

                done = False

                if self.experiments_failed_counter >= 5:

                    self.logger.info('Game over, restarting state...')

                    # Game over, start again
                    self.episodes_counter += 1
                    self.total_reward = 0
                    self.total_time_consumed = 0
                    self.executed_experiments_counter = 0
                    self.experiments_failed_counter = 0
                    self.last_reward = 0
                    reward = 0

                    # TODO: Check to be flexible
                    self.last_parameter_executed = 0.1

                    done = True

                    next_state = np.array(
                        [self.total_reward, self.total_time_consumed, self.executed_experiments_counter]).reshape(1, 3)

                    agent.replay()

                else:
                    self.logger.info('Continue playing...')

                    reward = self.check_reward(experiment_id)

                    self.logger.info('Reward: %f', reward)

                    time_consumed = self.check_time_consumed(experiment_id)

                    next_state = self.calculate_state(time_consumed, reward)

                    self.logger.info('Next state: %s', next_state)

                # Binary Reward means:
                # Binary_reward = 1 if value increase
                # Binary_reward = 0 if value decrease
                # Goal: Maximum value

                binary_reward = self.calc_reward(self.last_reward, reward)

                self.logger.info('Binary reward: %d', binary_reward)

                self.last_reward = reward

                # Save step
                agent.record(self.state, self.last_action, binary_reward, next_state, done)

                # Update state
                self.state = next_state

                # Choose next action
                action = self.run_reinforcement(agent)

                self.logger.info('Next action: %d', action)

                # Generate experiment and send to queue
                self.generate_experiments(action)

    def generate_experiments(self, action):
        """
        Generate new experiments to be sent to the queue and executed.
        :return: list
        """
        self.logger.info('Generating new experiment...')
        # TODO: Change to be flexible with different parameters
        current_value = self.last_parameter_executed
        experiments_to_queue = list()

        # Generate Experiments
        name = ''.join([self.project['name'], 'model{num}'.format(num=self.experiments_counter)])

        experiment = dict()
        experiment['name'] = name
        experiment['project_name'] = self.project['name']
        experiment['project_id'] = ObjectId(self.project_id)
        experiment['parameters'] = []
        experiment['create_time'] = datetime.datetime.utcnow()
        experiment['template_name'] = self.project['template']

        for param in self.project['parameters']:

            parameter = dict()

            if param['type'] == 'lineal':

                parameter['name'] = param['name']

                if action == 1:
                    # Increase 10%
                    value_to_execute = current_value * 1.1
                else:
                    # Decrease 10%
                    value_to_execute = current_value * 0.90

                parameter['value'] = value_to_execute
                self.last_parameter_executed = value_to_execute

            elif param['type'] == 'absolute':

                # TODO: Take more than just the first element
                parameter['name'] = param['name']
                parameter['value'] = param['value'][0]

            else:
                raise Exception("Parameter type not accepted")

            experiment['parameters'].append(parameter)
            self.logger.info('Experiment generated: %s', experiment)
        experiments_to_queue.append(experiment)

        # Send to the queue
        experiment_ids = super(DQLearning, self).send_experiments_to_queue(experiments_to_queue)

        # Append to running experiments
        self.running_experiments = self.running_experiments + experiment_ids

        # Increase the counter
        self.experiments_counter += 1

    def check_heuristic_syntax(self):
        """
        Check the heuristic section of the project definition.
        :return: boolean
        """
        self.logger.info('Checking project syntax definition...')
        for param in self.project['parameters']:
            if param['type'] == 'lineal':
                pass
            elif param['type'] == 'absolute':
                pass
            elif param['type'] == 'layers':
                raise Exception("Layers parameter still not implemented")
            else:
                raise Exception("Parameter type not accepted")

    def check_completed(self, experiment_id):
        """
        Check the status of the running experiments
        :return: boolean
        """
        # Check status
        state = str(self.db.get_document({'_id': ObjectId(experiment_id)}, "experiments")['state'])
        experiment_completed = \
            state == 'completed' \
            or state == 'accuracy_limit_reached' \
            or state == 'timeout'

        # If it is completed, delete from experiment list
        if experiment_completed:
            self.running_experiments.remove(experiment_id)

        # return true if it is completed
        return experiment_completed

    ###### RUN REINFORCEMENT #########

    def run_reinforcement(self, agent):

        action = agent.select_action(self.state)

        return action

    def calculate_state(self, time_consumed, reward):

        self.total_time_consumed = self.total_time_consumed + time_consumed
        self.total_reward = self.total_reward + reward
        self.executed_experiments_counter += 1

        state = np.array([self.total_time_consumed, self.total_reward, self.executed_experiments_counter]).reshape(1, 3)
        return state

    def calc_reward(self, previous_accuracy, current_accuracy):
        if previous_accuracy < current_accuracy:
            self.experiments_failed_counter = 0
            return 1
        else:
            self.experiments_failed_counter += 1
            return 0

    def check_time_consumed(self, experiment_id):
        """Return the experiment's execution time."""
        metrics = self.db.get_document(
            {'name': str(experiment_id) + '-metrics'}, 'experimentsMetrics')
        try:
            experiment_time = metrics['metrics'].pop()['experiment_time']
        except Exception:
            self.logger.debug('No metrics yet')
            experiment_time = 0
        return experiment_time

    def check_reward(self, experiment_id):
        """Return the experiment's execution time."""
        metrics = self.db.get_document(
            {'name': str(experiment_id) + '-metrics'}, 'experimentsMetrics')
        try:
            accuracy = metrics['metrics'].pop()['accuracy']
        except Exception:
            self.logger.debug('No metrics yet')
            accuracy = 0
        return accuracy


@task(name="deep_qlearning")
def start(project_id, model_id, total_n_episodes):
    db = DBConnector(MONGODB_URL, MONGODB_PORT,
                     MONGODB_DATABASE, MONGODB_USER,
                     MONGODB_PASSWORD)
    heuristic = DQLearning(project_id, model_id, total_n_episodes, db=db)
    heuristic.run()
