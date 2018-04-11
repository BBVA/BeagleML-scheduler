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
# coding=utf-8
"""Launch experiments through an orchestrator."""
import threading
import time
import datetime
import logging

from .experiment import Experiment
from .dal import DAL


class System(threading.Thread):
    def __init__(self, orchestrator, db, kafka_server):
        threading.Thread.__init__(self)

        self.logger = logging.getLogger("SCHEDULER")

        self.orch = orchestrator
        self.db = db
        self.dal = DAL(db)
        self.kafka_server = kafka_server

        self.is_running = False
        self.experiments_limit = 0
        self.experiments_running = 0

#        self.state_recovery()

    def state_recovery(self):
        """
        Recover the last state of the system.
        """
        # Update current state from DDBB
        system_parameters = self.dal.get_system_parameters()
        self.is_running = system_parameters['running']
        self.experiments_limit = system_parameters['experiments_limit']

        pool = self.dal.get_running_experiments()
        self.experiments_running = len(pool['running'])
        for experiment_in_pool in pool['running']:
            self.logger.warning('Experiments remaining in running pool.')
            self.logger.warning('Trying to recover control')

            experiment_info = self.dal.get_experiment(experiment_in_pool['experiment_id'])
            experiment = Experiment(experiment_info, self.kafka_server, self.db, self.orch)
            experiment.start()

            self.experiments_running += 1
            threading.Thread(target=experiment.control).start()
            self.logger.info(
                'Control recovered for experiment ' + experiment.name)

    def run(self):
        """
        Check the system status, and launch the experiments if possible.
        """
        self.logger.info('READY TO LAUNCH EXPERIMENTS !!!!')
        threading.Thread(target=self.monitor_running_experiments).start()

        while True:
            system_status = self.check_system()
            self.logger.debug("System " + str(system_status[1])
                              + " - Experiments: " + str(self.experiments_running)
                              + " running, " + str(self.experiments_limit) + " max.")
            if not system_status[0]:
                time.sleep(5)
                continue

            experiment_id = self.dal.retrieve_experiment_from_queue()
            if experiment_id:
                self.logger.info("Retrieved experiment " + str(experiment_id) + " from queue.")
                self.launch_experiment(experiment_id)
                self.logger.info('Experiment ' + str(experiment_id) + ' launched!!')
            else:
                self.logger.info('Queue empty.')
            time.sleep(5)

    def monitor_running_experiments(self):
        """Check periodically if there is space in the pool
        by querying current running experiments."""
        while True:
            time.sleep(10)
            running_list = self.dal.get_running_experiments()
            self.experiments_running = len(running_list["running"])

    def check_system(self):
        """
        Check the execution state of the system.

        The size of the pool, the number of experiments running and the
        activation of the system itself are checked periodically in order to
        manage the execution of the experiments.
        """
        system_config = self.dal.get_system_parameters()
        self.is_running = system_config['running']
        self.experiments_limit = system_config['experiments_limit']

        if not self.is_running:
            status = (False, 'paused')
        elif self.experiments_running >= self.experiments_limit:
            status = (False, 'full')
        else:
            status = (True, 'activated')

        return status

    def launch_experiment(self, experiment_id):
        """Launch the experiments stored in the execution queue."""
        self.logger.debug('Saving the launch time')
        launch_time = datetime.datetime.utcnow()

        self.dal.update_experiment_state(experiment_id, 'pool')
        self.dal.update_experiment_launch_time(experiment_id, launch_time)

        experiment_info = self.dal.get_experiment(experiment_id)

        self.logger.debug('Saving experiment in execution list')
        self.dal.save_running_experiment(experiment_info)

        self.logger.info('Launching experiment ' + str(experiment_id))
        experiment = Experiment(
            experiment_info, self.kafka_server, self.db, self.orch)
        experiment.start()
        self.experiments_running += 1
        threading.Thread(target=experiment.control).start()
