

pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        IMAGE_REPO = 'sathishdevops2004/food-hotel-app'
        DOCKER = 'C:\\Users\\acer\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
    }

    stages {
        stage('Build') {
            steps {
                bat '"%DOCKER%" build -t %IMAGE_REPO%:%BUILD_NUMBER% .'
            }
        }

        stage('Test') {
            steps {
                bat '"%DOCKER%" run --rm %IMAGE_REPO%:%BUILD_NUMBER% python -m pytest /app/backend/tests -q'
            }
        }

        stage('Publish') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub',
                        usernameVariable: 'REGISTRY_USER',
                        passwordVariable: 'REGISTRY_PASSWORD'
                    )
                ]) {
                    bat '''
                        @echo off
                        echo %REGISTRY_PASSWORD% | "%DOCKER%" login -u %REGISTRY_USER% --password-stdin
                        "%DOCKER%" push %IMAGE_REPO%:%BUILD_NUMBER%
                        "%DOCKER%" logout
                    '''
                }
            }
        }
    }
}
