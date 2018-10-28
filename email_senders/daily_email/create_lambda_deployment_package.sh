cd daily-email-env/lib/python3.6/site-packages/
zip -r9 ../../../../EmailsLambdaDeploymentPackage.zip *
cd ../../../../
zip -g EmailsLambdaDeploymentPackage.zip send_daily.py
zip -g EmailsLambdaDeploymentPackage.zip email_helpers.py
aws lambda update-function-code --function-name hksTodayDailyEmailSender --zip-file EmailsLambdaDeploymentPackage.zip