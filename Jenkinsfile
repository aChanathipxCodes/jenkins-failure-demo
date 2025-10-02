pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.image('docker:25.0.3-cli').inside('-u root -v /var/run/docker.sock:/var/run/docker.sock') {
                        sh 'docker version'
                    }
                }
            }
        }

        stage('Run Semgrep') {
            steps {
                script {
                    docker.image('python:3.11-slim').inside('-v /var/run/docker.sock:/var/run/docker.sock') {
                        sh '''
                        pip install --no-cache-dir semgrep
                        semgrep --config=p/owasp-top-ten --config=p/python --severity "ERROR" --sarif --output security-reports/semgrep.sarif --error
                        '''
                    }
                }
            }
        }

        stage('Run Bandit (Python SAST)') {
            steps {
                script {
                    docker.image('python:3.11-slim').inside('-v /var/run/docker.sock:/var/run/docker.sock') {
                        sh '''
                        pip install --no-cache-dir bandit
                        bandit -r . -ll -f json -o security-reports/bandit.json || true
                        '''
                    }
                }
            }
        }

        stage('Publish Reports') {
            steps {
                echo 'Scan completed. Reports archived in security-reports/'
            }
        }
    }

    post {
        always {
            echo 'This is always executed after the build'
        }

        success {
            echo 'Build completed successfully'
        }

        failure {
            echo 'Build failed'
        }
    }
}
