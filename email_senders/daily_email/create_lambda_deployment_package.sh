cd daily-email-env/lib/python3.6/site-packages/
zip -r9 ../../../../EmailsLambdaDeploymentPackage.zip *
cd ../../../../
zip -g EmailsLambdaDeploymentPackage.zip send_daily.py
zip -g EmailsLambdaDeploymentPackage.zip send_daily_helpers.py