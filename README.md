# Microservice
Microservice scenario in our bachelor project

# Testing
Main branch is automaticly tested when updated
Other branches are tested if they have a pull request towards the main branch
Testing runs the pytests and checks for linting errors using flake8
To run tests locally just run tox
Tox takes a while to finish, run once it before pushing to github

# Setup
This section explains how to setup a development enviroment for this project

## Virtual environment
1. Clone repository: `git clone git@github.com:Group-13-Bachelor/Microservice.git microservice`
2. Enter the repository: `cd microservice`
3. Create virutal environment: `python -m venv ./.venv`
4. Activate virutal environment:
    - Windows: `.venv\Scripts\activate.bat`
    - Linux: `source .venv/bin/activate`

## Install package
1. Stand in project root directory: `cd <path to directory>/microservice/`
2. Install project packages: `pip install -e .`
    - This also installs packages in `requirements.txt`
3. Install developer tools: `pip install -r .\requirements_dev.txt`

## Note
If you add another package to requirements.txt reinstall with pip
If you want to create another package create a folder in './src/' and add the package to the setup.cfg packages