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
import itertools
import numpy
import logging

logger = logging.getLogger("SCHEDULER")


def generate_lineal_parameter(parameter_values):
    """Generate parameters list for lineal parameter type."""
    initial_value = parameter_values['initial_value']
    final_value = parameter_values["final_value"]
    interval = parameter_values["interval"]
    param_options = numpy.arange(
            initial_value, final_value, interval)
    return param_options.tolist()


def generate_layers_parameter(parameter_values):
    """Generate parameters list for layers parameter type."""
    combinations = []
    number_layers = parameter_values['number_layers']
    number_units = parameter_values['number_units']
    for i in number_layers:
        for combination in itertools.product(number_units, repeat=i):
            combinations.append(','.join(map(str, list(combination))))
    return combinations


def generate_absolute_parameter(parameter_values):
    """Generate parameters list for absolute parameter type."""
    return parameter_values


parameters_types = {
    'lineal': generate_lineal_parameter,
    'layers': generate_layers_parameter,
    'absolute': generate_absolute_parameter
}


def check_parameter_type(parameter):
    return True if parameter in parameters_types.keys() else False


def get_parameters_from_project_definition(project_definition):
    """
    Transform parameters from the project definition into 2 lists.

    :param project_definition:
    :return: parameter_names        List of parameter names
    :return: parameter_values       List of parameter values
    """
    param_names = list()
    param_type_values = list()
    logger.debug("-- get_parameters_from_project_definition --")
    logger.debug(project_definition)

    for param in project_definition:
        logger.info(param)

        if param['name']:
            param_names.append(param['name'])

            if param['type'] and param['value']:
                param_type_values.append(
                    parameters_types[param['type']](param['value']))

    param_names = param_names[::-1]
    param_type_values = param_type_values[::-1]

    return param_names, param_type_values


def get_parameters_from_model_template(param_names, param_type_values, model_template):
    """
    Add default parameters to the user-defined parameters.

    The func adds the defaults values in the parameters not specified in
    the parameter list given in the arguments.
    """
    logger.info(model_template)
    for service_name, service_info in model_template.items():
        try:
            default_parameters = model_template[service_name]['parameters']
        except KeyError:
            logger.error('Json format does not contains a list of parameters as expected:'
                         ' [{\'name\': \'param_name\', \'value\': \'param_value\'},...]')
            raise

        try:
            for default_param in default_parameters:
                if default_param['name'] not in param_names:
                    param_names.append(default_param['name'])
                    list_elements = list()
                    list_elements.append(default_param['value'])
                    param_type_values.append(list_elements)
        except KeyError:
            logger.error('There are parameters without default value')
            raise

    return param_names, param_type_values


if __name__ == "__main__":
    import yaml
    template_name = 'test_paramameters_generator'
    input_string_parameters = """
      - name: HIDDEN_SIZE
        type: layers
        value:
          number_layers:
            - 1
            - 2
          number_units:
            - 20
            - 50
      - name: LEARNING_RATE
        type: lineal
        value:
            initial_value: 0.01
            final_value: 0.1
            interval: 0.05
      - name: TEST_SIZE
        type: absolute
        value:
          - 5
    """

    input_yaml_parameters = yaml.load(input_string_parameters)
    param_names, param_type_values = get_parameters_from_project_definition(input_yaml_parameters)
    param_names, param_type_values = get_parameters_from_model_template(
            param_names, param_type_values, template_name)
    print(param_names, param_type_values)
