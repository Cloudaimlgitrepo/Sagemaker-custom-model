# cell 01_ Dockerfile

!unzip scikit_bring_your_own.zip
!mv scikit_bring_your_own/data/ ./lab03_data/
!mv scikit_bring_your_own/container/ ./lab03_container/
!rm -rf scikit_bring_your_own
!cat lab03_container/Dockerfile

# cell 02_Building and registering container
!pip install sagemaker-studio-image-build

%%sh
# cell 03


cd lab03_container

chmod +x decision_trees/train
chmod +x decision_trees/serve

sm-docker build .  --repository sagemaker-decision-trees:latest

# cell 04_Using container

# S3 prefix
prefix = 'demo-scikit-byo-iris-prachi-09'

# Define IAM role
import boto3
import re

import os
import numpy as np
import pandas as pd
from sagemaker import get_execution_role

role = get_execution_role()

# cell 05

import sagemaker as sage
from time import gmtime, strftime

sess = sage.Session()

# cell 06

WORK_DIRECTORY = 'lab03_data'

data_location = sess.upload_data(WORK_DIRECTORY, key_prefix=prefix)

# cell 07

account = sess.boto_session.client('sts').get_caller_identity()['Account']
region = sess.boto_session.region_name
image = '{}.dkr.ecr.{}.amazonaws.com/sagemaker-decision-trees:latest'.format(account, region)

tree = sage.estimator.Estimator(image,
                       role, instance_count=1, instance_type='ml.c4.2xlarge',
                       output_path="s3://{}/output".format(sess.default_bucket()),
                       sagemaker_session=sess)
file_location = data_location + '/iris.csv'
tree.fit(file_location)

# cell 08_Hosting model
from sagemaker.serializers import CSVSerializer
predictor = tree.deploy(initial_instance_count=1, instance_type='ml.m4.xlarge', serializer=CSVSerializer())

# cell 09_Preparing test data to run inferences

shape=pd.read_csv(file_location, header=None)
shape.sample(3)

# cell 10

# drop the label column in the training set
shape.drop(shape.columns[[0]],axis=1,inplace=True)
shape.sample(3)

# cell 11

import itertools

a = [50*i for i in range(3)]
b = [40+i for i in range(10)]
indices = [i+j for i,j in itertools.product(a,b)]

test_data=shape.iloc[indices[:-1]]

# cell 12_Run predictions

print(predictor.predict(test_data.values).decode('utf-8'))

# cell 13_Cleanup
sess.delete_endpoint(predictor.endpoint_name)

# cell 14
!rm -rf lab03_container lab03_data


