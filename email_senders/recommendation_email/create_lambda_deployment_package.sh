cd recommendation-email-env/lib/python3.6/site-packages/
zip -r9 ../../../../RecEmailsLambdaDeploymentPackage.zip *
cd ../../../../
zip -g RecEmailsLambdaDeploymentPackage.zip send_recommendation.py
zip -g RecEmailsLambdaDeploymentPackage.zip email_helpers.py

aws s3 cp RecEmailsLambdaDeploymentPackage.zip s3://elasticbeanstalk-us-east-1-811388761146/lambda_function_code/
aws lambda update-function-code --function-name weeklyRecommedationEmail --zip-file fileb://RecEmailsLambdaDeploymentPackage.zip