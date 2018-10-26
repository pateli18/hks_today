docker build --rm --no-cache -t lambda-recommendations .

container_id=$(docker create lambda-recommendations bash)
docker cp $container_id:/var/task/RecsLambdaDeploymentPackage.zip .
docker rm -v $container_id

aws s3 cp RecsLambdaDeploymentPackage.zip s3://elasticbeanstalk-us-east-1-811388761146/lambda_function_code/