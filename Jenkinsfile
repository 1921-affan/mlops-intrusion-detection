pipeline {
    agent any

    environment {
        DOCKER_BUILDKIT = '1'
    }

    stages {

        stage('Lint') {
            steps {
                echo "🔍 Running lint checks..."
                sh '''
                python - <<EOF
import compileall
ok = compileall.compile_dir("src", quiet=1)
if not ok:
    raise SystemExit("Lint failed")
EOF
                '''
            }
        }

        stage('Test') {
            steps {
                echo "🧪 Running unit tests..."
                sh '''
                pytest tests
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

        stage('Restart Services') {
            steps {
                echo "♻ Restarting services..."
                sh '''
                docker compose down
                docker compose up -d
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully"
        }
        failure {
            echo "❌ Pipeline failed — check logs"
        }
    }
}
