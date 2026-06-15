pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    environment {
        // Jenkins Credentials IDs — add these in Jenkins → Manage → Credentials
        EC2_HOST = credentials('EC2_HOST')           // EC2 public IP string
        EC2_SSH_KEY = credentials('EC2_SSH_KEY')     // SSH private key (.pem content)
    }

    // Pipeline runs on manual 'Build Now' only — no auto-trigger on push


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
                  --volumes-from jenkins \
                  -w "$WORKSPACE" \
                  python:3.11 \
                  python -m compileall src
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo "🧪 Running unit tests..."
                sh '''
                docker run --rm \
                  --volumes-from jenkins \
                  -w "$WORKSPACE" \
                  python:3.11 \
                  sh -c "pip install pytest pyyaml && pytest tests/ -v"
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                echo "🐳 Building Docker images locally to verify build..."
                sh '''
                docker compose build
                '''
            }
        }


        stage('Deploy to EC2') {
            steps {
                echo "🚀 Deploying to AWS EC2..."
                sshagent(credentials: ['EC2_SSH_KEY']) {
                    sh '''
                    ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} "
                      set -e
                      cd ~/mlops-intrusion-detection
                      git pull origin master
                      docker compose down
                      docker compose up --build -d
                      sleep 5
                      docker compose ps
                      echo '✅ Deployment complete'
                    "
                    '''
                }
            }
        }
    }


    post {
        success {
            echo "✅ CI/CD pipeline completed successfully — app is live on EC2!"
        }
        failure {
            echo "❌ Pipeline failed — check logs above for details"
        }
    }
}
