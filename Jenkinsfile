

pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        IMAGE_REPO = 'sathishdevops2004/food-hotel-app'
    }

    stages {
        stage('Build') {
            steps {
                bat 'docker build -t %IMAGE_REPO%:%BUILD_NUMBER% .'
            }
        }

        stage('Test') {
            steps {
                bat 'docker run --rm %IMAGE_REPO%:%BUILD_NUMBER% python -m pytest /app/backend/tests -q'
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
                        echo %REGISTRY_PASSWORD% | docker login -u %REGISTRY_USER% --password-stdin
                        docker push %IMAGE_REPO%:%BUILD_NUMBER%
                        docker logout
                    '''
                }
            }
        }
    }
}
