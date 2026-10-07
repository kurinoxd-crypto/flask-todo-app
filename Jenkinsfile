pipeline {
    agent any

    environment {
        DOCKERHUB_USERNAME = 'kurinoxd'
        IMAGE_NAME         = "${DOCKERHUB_USERNAME}/flask-todo-app"
        IMAGE_TAG          = "${IMAGE_NAME}:${env.BUILD_NUMBER}"

        // Full paths because Jenkins service doesn't inherit your user PATH
        PYTHON = 'C:\\Users\\harit\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'
        PIP    = 'C:\\Users\\harit\\AppData\\Local\\Programs\\Python\\Python311\\Scripts\\pip.exe'
        DOCKER = 'C:\\Users\\harit\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
    }

    stages {

        // ── 1. Pull latest code from GitHub ───────────────────────────────────
        stage('Checkout') {
            steps {
                git url: 'https://github.com/kurinoxd-crypto/flask-todo-app.git',
                    branch: 'main',
                    credentialsId: 'github-credentials-id'
                bat "dir"
            }
        }

        // ── 2. Install Python dependencies ────────────────────────────────────
        stage('Setup') {
            steps {
                bat "\"%PIP%\" install -r requirements.txt"
            }
        }

        // ── 3. Unit tests ──────────────────────────────────────────────────────
        stage('Unit Tests') {
            steps {
                bat "\"%PYTHON%\" -m pytest test_app.py -v --tb=short"
            }
        }

        // ── 4. Selenium UI tests ───────────────────────────────────────────────
        stage('Selenium UI Tests') {
            steps {
                script {
                    bat "\"%PYTHON%\" start_flask.py"
                    try {
                        // conftest.py writes test_results.json automatically
                        bat "\"%PYTHON%\" -m pytest test_selenium.py -v"
                    } finally {
                        bat "\"%PYTHON%\" stop_flask.py || exit 0"
                    }
                    // Generate the custom HTML dashboard from test_results.json
                    bat "\"%PYTHON%\" generate_report.py"
                }
            }
            post {
                always {
                    publishHTML(target: [
                        allowMissing         : false,
                        alwaysLinkToLastBuild: true,
                        keepAll              : true,
                        reportDir            : '.',
                        reportFiles          : 'selenium_report.html',
                        reportName           : 'Selenium Test Report',
                        reportTitles         : 'Selenium Test Report'
                    ])
                }
            }
        }

        // ── 5. Log in to Docker Hub ────────────────────────────────────────────
        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId   : 'dockerhub-credentials-id',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat 'powershell -Command "$env:DOCKER_PASS | & \'%DOCKER%\' login -u $env:DOCKER_USER --password-stdin"'
                }
                echo 'Docker Hub login successful'
            }
        }

        // ── 6. Build Docker image ──────────────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                bat "\"%DOCKER%\" build -t ${IMAGE_TAG} ."
                bat "\"%DOCKER%\" images"
            }
        }

        // ── 7. Push to Docker Hub ──────────────────────────────────────────────
        stage('Push Docker Image') {
            steps {
                bat "\"%DOCKER%\" push ${IMAGE_TAG}"
                bat "\"%DOCKER%\" tag ${IMAGE_TAG} ${IMAGE_NAME}:latest"
                bat "\"%DOCKER%\" push ${IMAGE_NAME}:latest"
                echo "Pushed ${IMAGE_TAG} and ${IMAGE_NAME}:latest to Docker Hub"
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded - build #${env.BUILD_NUMBER} pushed to Docker Hub."
        }
        failure {
            echo "Pipeline failed. Check Console Output and the Selenium Test Report."
        }
        always {
            script {
                try {
                    bat "\"%DOCKER%\" rmi ${IMAGE_TAG} || exit 0"
                } catch (err) {
                    echo "Image cleanup skipped: ${err.message}"
                }
            }
        }
    }
}
