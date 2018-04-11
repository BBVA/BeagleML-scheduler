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
"""Module which holds the abstraction and control for a experiment."""
import queue
import time
import threading
import logging
import pdb

from .kafka_producer import KafkaProducer
from .dal import DAL


class Experiment:
    """Class which represents and control the lifecycle of a experiment."""

    def __init__(self, experiment, kafka_server, db, orchestrator):
        """Initialize the experiment."""
        self.name = experiment["name"]
        self.id = experiment["_id"]
        self.create_time = experiment["create_time"]
        self.project_name = experiment["project_name"]
        self.project_id = experiment["project_id"]
        self.state = experiment["state"]
        self.template_name = experiment["template_name"]
        self.time_out = experiment["time_out"]
        self.accuracy_limit = experiment["accuracy_limit"]
        self.parameters = experiment["parameters"]

        self.accuracy = 0
        self.queue_experiment = queue.Queue()
        self.start_time = None
        self.experiment_time = 0
        self.objective_function = None
        self.objective_result = None

        self.kafka_producer = KafkaProducer(kafka_server, self.queue_experiment)
        self.dal = DAL(db)
        self.orch = orchestrator
        self.logger = logging.getLogger("SCHEDULER")

    def start(self):
        """Launch an experiment using an orchestrator."""
        model_template = self.dal.get_model(self.template_name)
        orchestrator_output = self.orch.start_service(self.name, self.parameters, model_template)
        self.set_objective()
        if orchestrator_output == "error":
            time.sleep(60)
            self.state = "failed"
#           self.dal.update_running_experiment_state(self.id, "failed")
        else:
            self.start_time = time.time()
            self.state = "pool"
#            self.dal.update_running_experiment_state(self.id, "pool")  ##
            self.communicate_kafka("start")

    def set_objective(self):
        """Set the criteria to optimize the experiment."""
        project = self.dal.get_project(self.project_id)
        self.objective_function = project["optimization"]["objective_function"]
        self.objective_result = project["optimization"]["objective_result"]

    def communicate_kafka(self, action, state=None):
        """
        Publish a message to be consumed by automodeling monitor.
        If action is:
            "start": the message contains the 'topic name' where the experiment
            is going to publish metrics.
            The monitor will read metrics from it.

            "stop": the message contains the reason of stop consuming messages.
            The monitor will do it and kill the correspondent thread.
        """
        message = str(self.id)+'-metrics'
        if action == "start":
            threading.Thread(
                target=self.kafka_producer.send_topic,
                args=['scheduler-monitor', message]).start()

        if action == "stop":
            payload = "<STOPPED>"
            if state == "timeout":
                payload = "<TIMEOUT_REACHED>"
            if state == 'accuracy_limit_reached':
                payload = '<ACCURACY_REACHED>'
            if state == 'completed':
                payload = '<EXPERIMENT_COMPLETED>'
            threading.Thread(
                target=self.kafka_producer.send_topic,
                args=[message, payload]).start()

    def control(self):
        """Manage the execution of a experiment."""
        execution_deadline = self.start_time + self.time_out
        while time.time() <= execution_deadline and self.state == "pool":
            # Log experiment execution info.
            self.state = self.dal.get_experiment_state(self.id)
            self.logger.info(
                'Control experiment ' + str(self.name)
                + ' | State: ' + str(self.state)
                + ' | Remaining time: ' + str(execution_deadline - time.time())
                + ' | Accuracy: ' + str(self.accuracy))

            # Check if experiment reached accuracy limit.
            self.accuracy = self.dal.get_accuracy(self.id)
            if self.accuracy >= self.accuracy_limit:
                self.state = "accuracy_limit_reached"
                # TODO update ddbb
                self.logger.info("Accuracy limit: " + str(self.accuracy_limit) + " reached!!")

            # Check kafka response
            if self.get_kafka_response() == "error":
                self.state = "failed"
                # TODO update ddbb
                self.logger.critical('EXPERIMENT FAILED  |  STATE: ' + self.state)

            time.sleep(2)

        if self.state not in ("completed", "stopped", "accuracy_limit_reached", "failed"):
            self.state = "timeout"

        self.logger.info('Experiment ' + self.name +
                         ' ended!! Accuracy: ' + str(self.accuracy) +
                         ' (accuracy limit ' + str(self.accuracy_limit) +
                         '); State: ' + self.state)

        self.stop()

    def get_kafka_response(self):
        """Get the kafka response for the message sent."""
        try:
            response = self.queue_experiment.get(False)
        except queue.Empty:
            response = None
        return response

    def send_experiment_to_queue(self):
        """Sends experiment to experiments not-started queue. Used when a experiment does not end for kafka failure."""
        self.logger.critical('PUSHING EXPERIMENT ' + self.name + 'AGAIN TO THE QUEUE  |   STATE: ' + self.state)
        self.dal.send_experiment_to_queue(self.id)
        self.logger.critical('EXPERIMENT ' + self.name + 'IS AGAIN IN THE QUEUE  |   STATE: ' + self.state)

    def stop(self):
        """Stop a experiment."""
        self.logger.info('STOPPING EXPERIMENT ' + self.name + '  |   STATE: ' + self.state)
        self.logger.info('Deleting experiment ' + self.name + ' from running experiment list.')
        self.dal.delete_experiment_from_running_queue(self.id)

        orchestrator_output = self.orch.remove_service(self.name)
        if orchestrator_output == "error":
            self.logger.critical('ERROR RETURNED FROM ORCHESTRATOR')
            time.sleep(60)

        if self.state != "failed":
            self.communicate_kafka("stop", self.state)
            self.logger.info("Saving experiment " + self.name + " results to DDBB.")
            self.dal.save_experiment_result(self.project_id, self.id, self.accuracy)
        else:
            self.send_experiment_to_queue()
            self.logger.info("Experiment " + self.name + " failed. Sending again to queue.")

        self.logger.info('Updating experiment ' + self.name + ' state')
        self.dal.update_experiment_state(self.id, self.state)
        self.logger.info('Experiment ' + self.name + ' updated to state: ' + self.state)
