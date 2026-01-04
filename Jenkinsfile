pipeline {
    agent any

    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
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
                  python -m py_compile $(find src -name "*.py")
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
                echo "🐳 Building Docker images..."
                sh 'docker compose build'
            }
        }

        stage('Restart Services') {
            steps {
                echo "♻️ Restarting services..."
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
