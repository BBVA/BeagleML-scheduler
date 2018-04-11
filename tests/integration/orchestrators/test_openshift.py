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

from scheduler.orchestrators.openshift import OpenShift


@pytest.fixture()
def setup():
    # Iniatilize variables
    setup = dict()

    orchestrator = 'OpenShift'
    # URL and TOKEN can be retrieved via UI
    # https://<IP>:8443/console  > admin/developer > Copy Login Command > Paste in terminal
    url = 'https://192.168.64.3:8443'
    token = "tqiVPEM1TMy5ESnSngnvygTWMfZlJzloR-tQIjmvUVs"

    setup['orch'] = OpenShift(url, token)

    setup['name'] = 'helloworld'
    setup['parameters'] = [
        {'name': 'PARAM_1', 'value': "0.14507172892908632"},
        {'name': 'PARAM_2', 'value': '5aba5aaf716dff56b930e7f0-metrics'}
    ]

    # Example of template for OpenShift
    setup['template'] = {
        'kind': 'Template',
        'apiVersion': 'v1',
        'objects': [
            {
                'kind': 'DeploymentConfig',
                'apiVersion': 'v1',
                'spec': {
                    'replicas': 1,
                    'template': {
                        'spec':{
                            'containers': [
                                {
                                    'command': 'sleep 100',
                                    'env':[
                                        {'name': 'PARAM_1', 'value': 'PARAM_1_VALUE'},
                                        {'name': 'PARAM_2', 'value': 'PARAM_2_VALUE'}
                                    ],
                                    'image': 'hello-world'
                                }

                            ]
                        }
                    }
                }

            }
        ],
        '_id': ObjectId('5aba5aa5716dff56c658daff')
    }

    return setup


@pytest.mark.integration
@pytest.mark.openshift
def test_openshift_integration(setup):
    setup['orch'].login()
    started = setup['orch'].start_service(setup['name'], setup['parameters'], setup['template'])
    time.sleep(10)
    removed = setup['orch'].remove_service(setup['name'])
    time.sleep(2)

    assert started == "success"
    assert removed == "success"
