cd recommendation-email-env/lib/python3.6/site-packages/
zip -r9 ../../../../RecEmailsLambdaDeploymentPackage.zip *
cd ../../../../
zip -g RecEmailsLambdaDeploymentPackage.zip send_recommendation.py
zip -g RecEmailsLambdaDeploymentPackage.zip email_helpers.py
aws lambda update-function-code --function-name weeklyRecommedationEmail --zip-file RecEmailsLambdaDeploymentPackage.zip