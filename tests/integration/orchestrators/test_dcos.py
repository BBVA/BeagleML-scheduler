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
import time
import pytest

from bson.objectid import ObjectId

from scheduler.orchestrators.dcos import Dcos


@pytest.fixture()
def setup():
    # Iniatilize variables
    setup = dict()

    orchestrator = 'DCOS'
    url = 'http://localhost:5050'
    token = "no_login_needed"
    marathon_url = 'http://127.0.0.1:8080'

    setup['orch'] = Dcos(url, token, marathon_url=marathon_url)

    setup['name'] = 'helloworld'
    setup['parameters'] = [
        {'name': 'PARAM_1', 'value': "0.14507172892908632"},
        {'name': 'PARAM_2', 'value': '5aba5aaf716dff56b930e7f0-metrics'}
    ]

    # Example of template for DCOS
    setup['template'] = {
        'filename': 'algorithm.yaml',
        '_id': ObjectId('5aba5aa5716dff56c658daff'),
        'cmd': 'sleep 100',
        'env': {
            'PARAM_1': '0.1',
            'PARAM_2': 'metrics'
        },
        'container': {
            'type': 'DOCKER',
            'docker': {
                'image': 'hello-world'
                }
        },
        'instances': 1,
        'cpus': 1,
        'mem': 64
    }

    return setup


@pytest.mark.integration
@pytest.mark.dcos
def test_dcos_integration(setup):
    setup['orch'].login()
    started = setup['orch'].start_service(setup['name'], setup['parameters'], setup['template'])
    time.sleep(10)
    removed = setup['orch'].remove_service(setup['name'])
    time.sleep(2)

    assert started
    assert removed
