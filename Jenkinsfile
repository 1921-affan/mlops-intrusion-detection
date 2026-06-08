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

    triggers {
        githubPush()               // fires instantly on GitHub webhook push
        pollSCM('H/5 * * * *')    // fallback: poll every 5 min if webhook misses
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

        stage('Approve Deployment') {
            steps {
                echo "⏳ Waiting for manual approval before deploying to production..."
                timeout(time: 30, unit: 'MINUTES') {
                    input(
                        message: """
🚀 Deploy to Production EC2?

All checks passed:
  ✅ Python syntax lint
  ✅ Unit tests (pytest)
  ✅ Docker images built

Review your changes before approving.
Aborting will NOT affect the running system.
                        """,
                        ok: 'Deploy Now',
                        submitter: 'admin'   // only admin can approve
                    )
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                echo "🚀 Deploying to AWS EC2..."
                sshagent(credentials: ['EC2_SSH_KEY']) {
                    sh '''
                    ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} << 'ENDSSH'
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
