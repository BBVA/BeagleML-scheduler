from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'VERSION')) as f:
    version = f.read().strip()

with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

with open(path.join(here, 'CHANGELOG.rst')) as f:
    long_description = "\n".join((long_description, f.read()))

with open(path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

# test_requirements = [str(ir.req) for ir in parse_requirements('requirements_test.txt', session=PipSession())]

setup(name='scheduler',
      version=version,
      author_email=["joseluis.lucas.simarro@bbva.com"],
      maintainer_email="joseluis.lucas.simarro@bbva.com",
      description='BeagleMl-scheduler: generate and execute experiments',
      author='BBVALabs',
      long_description=long_description,
      url="https://github.com/BBVA/automodeling-scheduler",
      packages=find_packages(),
      install_requires=requirements,
      include_package_data=True,
      entry_points={'console_scripts': [
          'scheduler-dev = scheduler.server:main',
          'scheduler-system = settings.system:start',
      ]}
      # test_suite = 'tests',
      # tests_require = test_requirements
      )
