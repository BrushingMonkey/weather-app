def COLOR_MAP = [
    'FAILURE' : 'danger',
    'SUCCESS' : 'good'
]

pipeline {
    agent {
        docker {
            label 'slave'
            image "rebachi/pipeline-slave:latest"
            args '-u 0:0 -v /var/run/docker.sock:/var/run/docker.sock'
            alwaysPull true
        }
    }
    environment {
        registry = "rebachi/eks"
        registryCredential = 'docker-hub-id-new'
        dockerImage = ''
        ec2User = 'ubuntu'
        projectDir = 'weather_app'
        ARGOCD_REPO = "http://51.21.15.188/argocd/argocd.git"
        GITLAB_CREDS = credentials('6143c2d2-c572-4b68-a1f9-d06522812420')
        
    }

    parameters {
        string(name: 'REPLICAS', defaultValue: '2', description: 'REPLICAS')
    }

    stages {
        stage("Checkout SCM") {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh 'pylint --output-format=parseable --fail-under=1 ./weather_project/*.py'
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    dockerImage = "${registry}:${env.BUILD_NUMBER}"
                    sh "docker build -t ${dockerImage} -t ${registry}:latest ."
                }
            }
        }

        stage('Push Image To DockerHub') {
            steps {
                script {
                    docker.withRegistry('', registryCredential) {
                        sh "docker push ${dockerImage}"
                        sh "docker push ${registry}:latest"
                    }
                }
            }
        }

        /*/
        stage('Connectivity Test') {
            steps {
                script {
                    def containerName = 'weather_app_container'
                    sh "docker run --name ${containerName} -d -p 5000:5000 ${dockerImage}"

                    def result = sh(script: "python3 check_connectivity.py", returnStatus: true)

                    if (result != 200) {
                        error "Connectivity test failed"
                    }

                    sh "docker stop ${containerName} || true"
                    sh "docker rm ${containerName} || true"
                }
            }
        }
        */

        stage('Update Deployment in ArgoCD Repo') {
            steps {
                script {
                    // Set Git to trust the directory
                    sh "git config --global --add safe.directory '*'"
                    
                    // Clone the ArgoCD repo
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: '*/main']],
                        userRemoteConfigs: [[
                            url: "${ARGOCD_REPO}",
                            credentialsId: '6143c2d2-c572-4b68-a1f9-d06522812420'
                        ]]
                    ])

                    // Update the deployment.yaml file and push changes
                    
                    sh """
                        # Update the image and replicas
                        yq e '.spec.template.spec.containers[0].image = "${dockerImage}"' -i deployment.yaml
                        yq e '.spec.replicas = ${params.REPLICAS}' -i deployment.yaml
                        
                        # Configure Git user
                        git config user.email "jenkins@example.com"
                        git config user.name "Jenkins"
                        
                        # Commit changes
                        git add deployment.yaml
                        git commit -m "Update deployment with image ${dockerImage} and ${params.REPLICAS} replicas"
                        
                        # Push changes with credentials
                        export GIT_ASKPASS="./git_ask_pass.sh"
                        git push origin HEAD:main
                    """
                }
            }
        }

        // stage('Deploy to EKS Cluster') {
        //     steps {
        //         script {
        //             def imageToUse = params.DOCKER_IMAGE ?: dockerImage
        //             withAWS(credentials: 'aws-credential', region: 'eu-north-1') {
        //                 sh """
        //                     echo 'Updating kubeconfig for EKS Cluster...'
        //                     aws eks --region eu-north-1 update-kubeconfig --name production-shlomis-cluster

        //                     echo 'ImagetoUse: ${imageToUse}''
                            
        //                     # update the image and replicas
        //                     yq -e '.spec.template.spec.containers[0].image = "${imageToUse}"' deployment.yaml
        //                     yq -e '.spec.replicas = ${REPLICAS}' deployment.yaml
                            
        //                     kubectl apply -f deployment.yaml
        //                 """
        //             }
        //         }
        //     }
        // }

    }

    post {
        success {
            slackSend(
                channel: '#succeeded-build',
                color: COLOR_MAP[currentBuild.currentResult],
                message: "*${currentBuild.currentResult}:* Job ${env.JOB_NAME} \n build ${env.BUILD_NUMBER} \n More info at: ${env.BUILD_URL}"
            )
        }
        failure {
            slackSend(
                channel: '#devops-alerts',
                color: COLOR_MAP[currentBuild.currentResult],
                message: "*${currentBuild.currentResult}:* Job ${env.JOB_NAME} \n build ${env.BUILD_NUMBER} \n More info at: ${env.BUILD_URL}"
            )
        }
        cleanup {
            sh "docker rmi ${registry}:latest || true"
            sh "find ${env.WORKSPACE} -mindepth 1 -delete" 
            deleteDir()
        }
    }
}
