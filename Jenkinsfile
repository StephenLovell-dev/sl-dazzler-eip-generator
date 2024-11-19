pipeline {
    agent any

    environment {
        PYVER = '3.12'
        POETRYVER = '1.8.4'
        PYENV_ROOT="$HOME/.pyenv"
        PATH = "${env.HOME}/.local/bin:/usr/local/bin:$PYENV_ROOT/bin:$PYENV_ROOT/shims:${env.PATH}"
        COVERAGE_MIN=76
    }

    stages {
        stage('Tooling') {
            steps {
                sh "[ -d $PYENV_ROOT ] || curl https://pyenv.run | bash"
                sh "pyenv install -s ${PYVER}"
                sh "pyenv local ${PYVER}"
                sh "poetry > /dev/null || curl -sSL https://install.python-poetry.org  | python - --version ${POETRYVER}"
                sh 'rm -rf dist package package.zip'
            }
        }
        stage('Test') {
            steps {
                sh "poetry env remove ${PYVER} || true"
                sh "poetry env use ${PYVER}"
                sh "poetry install"
	            sh 'poetry run coverage run --source=dazzler,log,medialivehelpers,dazzler_nexts_generator -m pytest'
                sh 'poetry run coverage report --fail-under=${COVERAGE_MIN}'
            }
        }
        stage('Build') {
            steps {
                sh "poetry env remove ${PYVER} || true"
                sh "poetry env use ${PYVER}"
                sh 'poetry build'
                sh 'poetry run pip install --upgrade -t package dist/*.whl'
                sh 'cd package; zip -r ../package.zip . -x *.pyc'
            }
        }
        stage('Release') {
            steps {
                script {
                    env.VERSION = sh( script: 'git tag --contains ${GIT_COMMIT}', returnStdout: true).replace('v', '')
                }
                sh 'cosmos-release lambda --lambda-version=${VERSION} package.zip ${JOB_NAME}'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying....'
                sh 'cosmos deploy-lambda --force ${JOB_NAME} test'
            }
        }
    }
}
