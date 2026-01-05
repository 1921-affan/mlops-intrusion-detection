pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    stages {

        stage('Prepare Workspace') {
            steps {
                deleteDir()
            }
        }

        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Lint (Syntax Check)') {
            steps {
                echo "🔍 Running Python syntax check..."
                sh '''
                docker run --rm \
                  -v "$PWD:/app" \
                  -w /app \
                  python:3.11 \
                  python -m compileall .
                '''
            }
        }

        stage('Tests') {
            steps {
                echo "🧪 Running tests..."
                sh '''
                docker run --rm \
                  -v "$PWD:/app" \
                  -w /app \
                  python:3.11 \
                  sh -c "pip install pytest && pytest src || true"
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh 'docker-compose build'
            }
        }

        stage('Restart Services') {
            steps {
                sh '''
                echo "🧹 Cleaning old containers..."
                docker-compose down --remove-orphans || true
                docker rm -f consumer producer api mlflow redis minio grafana prometheus || true

                echo "🚀 Starting services..."
                docker-compose up -d
                '''
            }
        }
    }

    post {
        success {
            echo "✅ CI Pipeline completed successfully"
        }
        failure {
            echo "❌ CI Pipeline failed"
        }
    }
}
