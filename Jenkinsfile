pipeline {
    agent any

    environment {
        // ── CHANGE THESE to your own values ───────────────────────────────────
        DOCKERHUB_USERNAME = 'kurinoxd'
        IMAGE_NAME         = "${DOCKERHUB_USERNAME}/flask-todo-app"
        IMAGE_TAG          = "${IMAGE_NAME}:${env.BUILD_NUMBER}"
        // ──────────────────────────────────────────────────────────────────────

        KUBECONFIG = credentials('kubeconfig-credentials-id')   // set up in step 3
    }

    stages {

        // ── 1. Pull latest code from YOUR GitHub repo ──────────────────────────
        stage('Checkout') {
            steps {
                git url: 'https://github.com/kurinoxd-crypto/flask-todo-app.git',
                    branch: 'main',
                    credentialsId: 'github-credentials-id'
                bat "dir"
            }
        }

        // ── 2. Install Python deps ─────────────────────────────────────────────
        stage('Setup') {
            steps {
                bat "pip install -r requirements.txt"
            }
        }

        // ── 3. Unit tests (pytest) ─────────────────────────────────────────────
        stage('Unit Tests') {
            steps {
                bat "pytest test_app.py -v --tb=short"
            }
        }

        // ── 4. Start app, run Selenium tests, stop app ─────────────────────────
        stage('Selenium UI Tests') {
            steps {
                script {
                    // Start Flask in background (Windows-compatible)
                    bat "start /B python app.py"
                    sleep 3  // give Flask a moment to boot

                    try {
                        bat """
                            set HEADLESS=true
                            set APP_URL=http://localhost:5000
                            pytest test_selenium.py --html=selenium_report.html --self-contained-html -v
                        """
                    } finally {
                        // Kill Flask after tests, pass or fail (Windows)
                        bat "taskkill /F /IM python.exe /T || exit 0"
                    }
                }
            }
            post {
                always {
                    // Archive the HTML report as a Jenkins build artifact
                    publishHTML(target: [
                        allowMissing         : false,
                        alwaysLinkToLastBuild: true,
                        keepAll              : true,
                        reportDir            : '.',
                        reportFiles          : 'selenium_report.html',
                        reportName           : 'Selenium Test Report'
                    ])
                }
            }
        }

        // ── 5. Log in to Docker Hub ────────────────────────────────────────────
        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId : 'dockerhub-credentials-id',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat 'echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin'
                }
                echo 'Docker Hub login successful'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat "docker build -t ${IMAGE_TAG} ."
                echo "Built image: ${IMAGE_TAG}"
                bat "docker images"
            }
        }

        stage('Push Docker Image') {
            steps {
                bat "docker push ${IMAGE_TAG}"
                bat "docker tag ${IMAGE_TAG} ${IMAGE_NAME}:latest"
                bat "docker push ${IMAGE_NAME}:latest"
                echo "Pushed ${IMAGE_TAG} and ${IMAGE_NAME}:latest"
            }
        }

        stage('Deploy to EKS') {
            steps {
                bat """
                    powershell -Command "(Get-Content deployment.yaml) -replace 'image: .*flask.*', 'image: ${IMAGE_TAG}' | Set-Content deployment.yaml"
                    kubectl apply -f deployment.yaml
                    kubectl rollout status deployment/flask-app-deployment-prod --timeout=120s
                """
                echo "Deployed ${IMAGE_TAG} to EKS cluster"
            }
        }
    }

    // ── Post-pipeline notifications ────────────────────────────────────────────
    post {
        success {
            echo "Pipeline succeeded - build #${env.BUILD_NUMBER} is live."
        }
        failure {
            echo "Pipeline failed. Check the Selenium Report artifact for UI test details."
        }
        always {
            bat "docker rmi ${IMAGE_TAG} || exit 0"
        }
    }
}
