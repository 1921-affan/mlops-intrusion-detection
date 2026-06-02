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
                echo "🧪 Running unit tests..."
                sh '''
                docker run --rm \
                  -v "$PWD:/app" \
                  -w /app \
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
                sh '''
                # Write the SSH key to a temp file
                mkdir -p ~/.ssh
                echo "${EC2_SSH_KEY}" > /tmp/ec2_key.pem
                chmod 600 /tmp/ec2_key.pem

                # Disable strict host key checking for automation
                ssh -o StrictHostKeyChecking=no \
                    -i /tmp/ec2_key.pem \
                    ubuntu@${EC2_HOST} << 'ENDSSH'
                    set -e
                    cd ~/mlops-intrusion-detection

                    # Pull latest code
                    git pull origin master

                    # Rebuild and restart all containers
                    docker compose down
                    docker compose up --build -d

                    # Quick sanity check
                    sleep 5
                    docker compose ps
                    echo "✅ Deployment complete"
ENDSSH
                # Clean up key
                rm -f /tmp/ec2_key.pem
                '''
            }
        }
    }

    post {
        success {
            echo "✅ CI/CD pipeline completed successfully — app is live on EC2!"
        }
        failure {
            echo "❌ Pipeline failed — check logs above for details"
            sh 'rm -f /tmp/ec2_key.pem || true'  // always clean up key on failure too
        }
    }
}
