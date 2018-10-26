FROM lambci/lambda:build-python3.6

COPY requirements.txt /requirements.txt
RUN cd /; mkdir lambda-libs
RUN pip install -t lambda-libs/ -r /requirements.txt

RUN cd lambda-libs; zip -r ../RecsLambdaDeploymentPackage.zip .

COPY generate_recommendations.py /generate_recommendations.py
RUN zip -g RecsLambdaDeploymentPackage.zip /generate_recommendations.py

COPY utils /utils
RUN zip -r -g RecsLambdaDeploymentPackage.zip /utils