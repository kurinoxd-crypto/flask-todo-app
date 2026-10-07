pipeline {
    agent any

    environment {
        DOCKERHUB_USERNAME = 'kurinoxd'
        IMAGE_NAME         = "${DOCKERHUB_USERNAME}/flask-todo-app"
        IMAGE_TAG          = "${IMAGE_NAME}:${env.BUILD_NUMBER}"
    }

    stages {

        // ── 1. Checkout from GitHub ────────────────────────────────────────────
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
                bat "pip install -r requirements.txt"
            }
        }

        // ── 3. Unit tests ──────────────────────────────────────────────────────
        stage('Unit Tests') {
            steps {
                bat "pytest test_app.py -v --tb=short"
            }
        }

        // ── 4. Selenium UI tests ───────────────────────────────────────────────
        stage('Selenium UI Tests') {
            steps {
                script {
                    bat "start /B python app.py"
                    sleep 3

                    try {
                        bat """
                            set HEADLESS=true
                            set APP_URL=http://localhost:5000
                            pytest test_selenium.py --html=selenium_report.html --self-contained-html -v
                        """
                    } finally {
                        bat "taskkill /F /IM python.exe /T || exit 0"
                    }
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
                        reportName           : 'Selenium Test Report'
                    ])
                }
            }
        }

        // ── 5. Docker Hub login ────────────────────────────────────────────────
        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId   : 'dockerhub-credentials-id',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat 'echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin'
                }
                echo 'Docker Hub login successful'
            }
        }

        // ── 6. Build Docker image ──────────────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                bat "docker build -t ${IMAGE_TAG} ."
                echo "Built image: ${IMAGE_TAG}"
                bat "docker images"
            }
        }

        // ── 7. Push to Docker Hub ──────────────────────────────────────────────
        stage('Push Docker Image') {
            steps {
                bat "docker push ${IMAGE_TAG}"
                bat "docker tag ${IMAGE_TAG} ${IMAGE_NAME}:latest"
                bat "docker push ${IMAGE_NAME}:latest"
                echo "Pushed ${IMAGE_TAG} and ${IMAGE_NAME}:latest"
            }
        }

        // ── 8. Deploy to AWS EKS (skipped until kubeconfig is configured) ──────
        stage('Deploy to EKS') {
            when {
                // Only run this stage if the kubeconfig file actually exists
                expression {
                    return fileExists("$WORKSPACE\\kubeconfig")
                }
            }
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-credentials-id', variable: 'KUBECONFIG')]) {
                    bat """
                        powershell -Command "(Get-Content deployment.yaml) -replace 'image: .*flask.*', 'image: ${IMAGE_TAG}' | Set-Content deployment.yaml"
                        kubectl apply -f deployment.yaml
                        kubectl rollout status deployment/flask-app-deployment-prod --timeout=120s
                    """
                }
                echo "Deployed ${IMAGE_TAG} to EKS cluster"
            }
        }
    }

    post {
        success {
            echo "Pipeline succeeded - build #${env.BUILD_NUMBER} is live."
        }
        failure {
            echo "Pipeline failed. Check Console Output and the Selenium Test Report for details."
        }
        always {
            script {
                // Only clean up the image if it was actually built
                if (env.IMAGE_TAG) {
                    bat "docker rmi ${IMAGE_TAG} || exit 0"
                }
            }
        }
    }
}
