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
import pytest
from scheduler import server


@pytest.fixture
def client(request):
    test_client = server.app.test_client()
    test_client.testing = True

    def teardown():
        pass

    request.addfinalizer(teardown)
    return test_client


def test_upload_model_template(client):
    response = client.post('/api/v1/upload')

    assert b'OK' in response.data
    assert response.status_code == 200


def test_upload_project_definition(client):
    pass
