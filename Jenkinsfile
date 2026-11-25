pipeline {
  agent any
  options { disableConcurrentBuilds(); timestamps() }
  environment {
    IMAGE_REPO = 'DOCKERHUB_USERNAME/ajith-food-corner'
  }
  stages {
    stage('Build') {
      steps { sh 'docker build -t "$IMAGE_REPO:$BUILD_NUMBER" .' }
    }
    stage('Test') {
      steps { sh 'docker run --rm "$IMAGE_REPO:$BUILD_NUMBER" python -m pytest /app/backend/tests -q' }
    }
    stage('Publish') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_PASSWORD')]) {
          sh 'set +x; echo "$REGISTRY_PASSWORD" | docker login -u "$REGISTRY_USER" --password-stdin; docker push "$IMAGE_REPO:$BUILD_NUMBER"; docker logout'
        }
      }
    }
    stage('Deploy') {
      steps {
        sshagent(credentials: ['ec2-ssh']) {
          sh 'IMAGE_NAME="$IMAGE_REPO:$BUILD_NUMBER" ansible-playbook -i ansible/inventory.ini ansible/deploy.yml'
        }
      }
    }
  }
}
