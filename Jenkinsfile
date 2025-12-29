pipeline {
    agent any

    environment {
        DOCKER_BUILDKIT = '1'
    }

    stages {

        stage('Lint') {
            agent {
                docker {
                    image 'python:3.10-slim'
                }
            }
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
            agent {
                docker {
                    image 'python:3.10-slim'
                }
            }
            steps {
                echo "🧪 Running unit tests..."
                sh '''
                pip install -r requirements.train.txt
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
