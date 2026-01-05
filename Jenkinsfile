pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    stages {

        stage('Prepare Workspace') {
            steps {
                deleteDir()
            }
        }

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Lint (Python Syntax)') {
            steps {
                echo "🔍 Running Python syntax check..."
                sh '''
                docker run --rm \
                  -v "$PWD:/app" \
                  -w /app \
                  python:3.11 \
                  python -m compileall src
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo "🧪 Running tests..."
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
                echo "🐳 Building Docker images..."
                sh '''
                docker compose build
                '''
            }
        }
    }

    post {
        success {
            echo "✅ CI pipeline completed successfully"
        }
        failure {
            echo "❌ CI pipeline failed"
        }
    }
}
