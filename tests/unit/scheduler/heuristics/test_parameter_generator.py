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
from scheduler.heuristics.grid import parameter_generator as pg

# EXAMPLES

example_model_template = dict(
    {
        'version': '2',
        'services': {
            'my_model_descriptive_name': {
                'image': 'my_model_in_docker:version',
                'environment': {
                    'TRAIN_FILE': 'input.txt',
                    'INPUT_SIZE': 10,
                    'HIDDEN_SIZE': '5',
                    'BATCH_SIZE': 100,
                    'LEARNING_RATE': 0.02,
                }
            }
        },
        'filename': 'dockercompose_MT_fakeMX.yml'
    }
)
#         '_id': ObjectId('5a31201b42e6900008c53a0f'),

example_project_definition = dict(
    {
        'timeOut': 160.0,
        'accuracy_limit': 0.98,
        'experimentsLimit': 1,
        'optimization': {
            'type': 'grid',
            'objective_function': 'experiment_time',
            'objectiveResult': 'min'
        },
        'project': [
            {'name': 'test_name',
             'template': 'test_template_file.yml',
             'parameters': [
                 {'type': 'absolute', 'value': ['data.csv'], 'name': 'TRAIN_FILE'},
                 {'type': 'absolute', 'value': [171], 'name': 'INPUT_SIZE'},
                 {'type': 'layers',   'value': {'number_units': [80, 50, 30], 'number_layers': [2]}, 'name': 'HIDDEN_SIZE'},
                 {'type': 'absolute', 'value': [1000, 5000], 'name': 'BATCH_SIZE'},
                 {'value': {'final_value': 0.03, 'initial_value': 0.01, 'interval': 0.01}, 'type': 'lineal', 'name': 'LEARNING_RATE'}
              ]
             }
        ]
    }
)

# TESTS

# Generate LINEAL Parameter
# {'value': {'final_value': 0.03, 'initial_value': 0.01, 'interval': 0.01}, 'type': 'lineal', 'name': 'LEARNING_RATE'}
input_lineal_parameter = dict(
    {
        'interval': 0.01,
        'final_value': 0.03,
        'initial_value': 0.01
    }
)
expected_lineal_parameters = [0.01, 0.02]


def test_generate_lineal_parameter():
    output = pg.generate_lineal_parameter(input_lineal_parameter)
    assert output == expected_lineal_parameters


# Generate LAYERS Parameter
# {'type': 'layers',   'value': {'number_units': [80, 50, 30], 'number_layers': [2]}, 'name': 'HIDDEN_SIZE'}
input_layers_parameter = dict(
    {
        'number_layers': [2],
        'number_units': [80, 50, 30]
    }
)
expected_layers_parameters = ['80,80', '80,50', '80,30', '50,80', '50,50', '50,30', '30,80', '30,50', '30,30']


def test_generate_layers_parameter():
    output = pg.generate_layers_parameter(input_layers_parameter)
    assert output == expected_layers_parameters
    assert len(output) == 9


# Generate ABSOLUTE Parameter
# {'type': 'absolute', 'value': [1000, 5000], 'name': 'BATCH_SIZE'},
input_absolute_parameter = [1000, 5000]
expected_absolute_parameter = [1000, 5000]


def test_generate_absolute_parameter():
    output = pg.generate_absolute_parameter(input_absolute_parameter)
    assert output == expected_absolute_parameter


# Get parameters from PROJECT DEFINITION
input_project_definition_parameters = [
    {'value': ['data.csv'], 'type': 'absolute', 'name': 'TRAIN_FILE'},
    {'value': [171], 'type': 'absolute', 'name': 'INPUT_SIZE'},
    {'value': {'number_layers': [2], 'number_units': [80, 50, 30]}, 'type': 'layers', 'name': 'HIDDEN_SIZE'},
    {'value': [1000, 5000], 'type': 'absolute', 'name': 'BATCH_SIZE'},
    {'value': {'final_value': 0.03, 'initial_value': 0.01, 'interval': 0.01}, 'type': 'lineal', 'name': 'LEARNING_RATE'}
]
expected_parameters_names = [
    'LEARNING_RATE',
    'BATCH_SIZE',
    'HIDDEN_SIZE',
    'INPUT_SIZE',
    'TRAIN_FILE'
]
expected_parameters_values = [
    [0.01, 0.02],
    [1000, 5000],
    ['80,80', '80,50', '80,30', '50,80', '50,50', '50,30', '30,80', '30,50', '30,30'],
    [171],
    ['data.csv']
]


def test_get_parameters_from_project_definition():
    parameter_names, parameter_values = pg.get_parameters_from_project_definition(input_project_definition_parameters)
    assert parameter_names == expected_parameters_names
    assert parameter_values == expected_parameters_values


# Get parameters from MODEL TEMPLATE
input_model_template_parameters = dict(
    {
        'my_model_descriptive_name': {
            'parameters': [
                {'name': 'TRAIN_FILE', 'value': 'input.txt'},
                {'name': 'INPUT_SIZE', 'value': 10},
                {'name': 'HIDDEN_SIZE', 'value': '5'},
                {'name': 'BATCH_SIZE', 'value': 100},
                {'name': 'LEARNING_RATE', 'value': 0.02}
            ]
        }
    }
)
expected_parameters_names_from_template = [
    'TRAIN_FILE',
    'INPUT_SIZE',
    'HIDDEN_SIZE',
    'BATCH_SIZE',
    'LEARNING_RATE'
]
expected_parameters_values_from_template = [
    ['input.txt'],
    [10],
    ['5'],
    [100],
    [0.02]
]


def test_get_parameters_from_model_template():
    parameter_names = []
    parameter_values = []

    parameter_names, parameter_values = \
        pg.get_parameters_from_model_template(parameter_names, parameter_values, input_model_template_parameters)

    assert parameter_names == expected_parameters_names_from_template
    assert parameter_values == expected_parameters_values_from_template


# MIX parameters from both files
