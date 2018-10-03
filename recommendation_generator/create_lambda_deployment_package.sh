cd recommendation-env/lib/python3.6/site-packages/
zip -r9 ../../../../RecsLambdaDeploymentPackage.zip *
cd ../../../../
zip -g RecsLambdaDeploymentPackage.zip generate_recommendations.py
zip -r -g RecsLambdaDeploymentPackage.zip utils