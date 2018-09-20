cd scraper-env/lib/python3.6/site-packages/
zip -r9 ../../../../ScraperLambdaDeploymentPackage.zip *
cd ../../../../
zip -g ScraperLambdaDeploymentPackage.zip scrapers.py
zip -g ScraperLambdaDeploymentPackage.zip run_scrapers.py