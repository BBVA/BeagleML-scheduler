# Heuristics

Heuristics are the -plugable- brain of beagleML.


## Current heuristics

#### Grid Search

It generates the full combination of experiments and send, in order, all of them to queue.

#### Random Search

It generates the full combination of experiments and send all of them to queue in a random way.

#### DQLearning

#### DDQLearning


## Developer guide

Heuristics interface provides developers with these methods:
* ```get_project_definition``` and ```get_model_template``` to retrieve the info. provided by the user through
project_definition and model template files.
* ```send_experiments_to_queue``` to queue a set of experiments in the main queue.

A developer interested in creating a certain heuristic must implement these other methods:
* check_heuristic_syntax: Validate heuristic configuration from project_definition file.
* generate_experiments: Generate new experiments to be sent to the queue and executed.
* evaluate: Manage the heuristic process until the search is finished.
* run: Launch the full heuristic search process

