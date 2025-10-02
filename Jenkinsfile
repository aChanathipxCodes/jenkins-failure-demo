pipeline {
    agent any
    environment {
        APP_FILE = 'app.py'  // Define the path to your app.py file
    }
    stages {
        stage('Install Dependencies') {
            steps {
                script {
                    // Install required dependencies (semgrep, bandit)
                    sh 'pip install -r requirements.txt'
                }
            }
        }
        stage('Checkout') {
            steps {
                // Checkout the code from GitHub for each build
                checkout scm
            }
        }
        stage('Scan Success') {
            steps {
                script {
                    // Run Semgrep scan on the app.py file (Success scenario)
                    echo "Running Semgrep scan on app.py for Success"
                    sh "semgrep --config=https://semgrep.dev/p/owasp-top-ten ${APP_FILE}"
                }
            }
        }
        stage('Scan Failure') {
            steps {
                script {
                    // Run Semgrep scan on the app.py file (Failure scenario)
                    echo "Running Semgrep scan on app.py for Failure"
                    sh "semgrep --config=https://semgrep.dev/p/owasp-top-ten --error ${APP_FILE}"
                }
            }
        }
        stage('Bandit Scan') {
            steps {
                script {
                    // Run Bandit scan on the app.py file (Optional, additional security checks)
                    echo "Running Bandit scan on app.py"
                    sh "bandit -r ${APP_FILE} -ll"
                }
            }
        }
    }
    post {
        always {
            cleanWs()  // Clean up workspace after the pipeline finishes
        }
    }
}
