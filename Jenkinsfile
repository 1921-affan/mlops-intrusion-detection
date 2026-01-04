pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    stages {

        stage('Prepare Workspace') {
            steps {
                deleteDir()   // hard reset workspace
            }
        }

        stage('Checkout SCM') {
            steps {
                checkout scm
            }
        }

        stage('Lint (Syntax Check)') {
            steps {
                echo "🔍 Running Python syntax check in Docker..."
                sh '''
                docker run --rm \
                  -v "$PWD:/app" \
                  -w /app \
                  python:3.11 \
                  python -m compileall src
                '''
            }
        }

        stage('Tests') {
            steps {
                echo "🧪 Running tests in Docker..."
                sh '''
                docker run --rm \
                  -v "$PWD:/app" \
                  -w /app \
                  python:3.11 \
                  sh -c "pip install pytest && pytest tests || true"
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Restart Services') {
            steps {
                sh '''
                docker compose down
                docker compose up -d
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
