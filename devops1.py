#!/usr/bin/env python3
#Code Created by: Renato Francisco Goedert
#Student Number: 20099697
#Improved using Chat GPT

import boto3
import botocore.exceptions
import webbrowser
import string
import random
import requests
import time
import os
import subprocess
from datetime import datetime, timedelta

######### ec2 #########


print ("Working...")

#ec2 resource creation
ec2 = boto3.resource("ec2")

#create an ec2 client
ec2_client = boto3.client('ec2')

#user data parameter>script to update and install Apache+index.html
user_data = """#!/bin/bash
yum update -y
yum install httpd -y
systemctl enable httpd
systemctl start httpd
cat <<EOF > /var/www/html/index.html
<html>
<head>
<title>Devops1 index page</title>
</head>
<body>
<h1>Welcome!</h1>
<p>This is my devops Assignment index page.</p>
<p>Done by Renato</p>
<p>Student Number: 20099697</p>
<p>Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>
<p>AMI ID: $(curl -s http://169.254.169.254/latest/meta-data/ami-id)</p>
<p>Instance Type: $(curl -s http://169.254.169.254/latest/meta-data/instance-type)</p>
</body>
</html>
EOF
"""

key_name = "my_key"

# Check if key pair already exists
try:
    ec2_client.describe_key_pairs(KeyNames=[key_name])
    print(f"Key pair '{key_name}' already exists. Skipping creation.")

except botocore.exceptions.ClientError as error:
    if error.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
# Create key pair if it doesn't exist
        key_pair = ec2_client.create_key_pair(KeyName=key_name)
#setting the  access permissions
        os.chmod(f"{key_name}.pem", 0o700)
        with open(f"{key_name}.pem", "w") as f:
            f.write(key_pair["KeyMaterial"])
#setting the  access permissions
        os.chmod(f"{key_name}.pem", 0o400)
        print (f"Key Created: {key_name}.pem")
    else:
        print (f"Error creating key pair: {error}")

group_name = "HTTP-Security-Group"

# Check if security group already exists
try:
    http_security_group = ec2_client.describe_security_groups(GroupNames=[group_name])["SecurityGroups"][0]
    print("Security group already exists. Skipping creation.")

except botocore.exceptions.ClientError as error:
    if error.response["Error"]["Code"] == "InvalidGroup.NotFound":
        http_security_group = ec2.create_security_group(
            GroupName=group_name,
            Description="Security group for HTTP traffic"
        )
#autorizing http for security group
        http_security_group.authorize_ingress(
            IpProtocol="tcp",
            FromPort=80,
            ToPort=80,
            CidrIp="0.0.0.0/0"
        )
#autorizing ssh for security group
        http_security_group.authorize_ingress(
            IpProtocol="tcp",
            FromPort=22,
            ToPort=22,
            CidrIp="0.0.0.0/0"
        )
        print ("Security group created!")
    else:
        print (f"Error creating security group: {error}")

#creating ec2 instance and adding parameters
try:
    instance = ec2.create_instances(
        ImageId="ami-0aa7d40eeae50c9a9",
        MinCount=1,
        MaxCount=1,
        KeyName="my_key",
        SecurityGroups=["HTTP-Security-Group"],
        InstanceType="t2.nano",
        UserData=user_data,
#Enabeling monitor to cloud watch
        Monitoring={
            "Enabled": True
        }
    )[0]

#waiting for the instance to run
    instance.wait_until_running()

#reloading the instance, updating state
    instance.reload()

#setting the ip adress and catching an error if IP address not created
    public_ip = instance.public_ip_address
    if not public_ip:
        print("Instance doesn't have a public IP address yet")
        exit()

#setting variable and printing ID and State
    ec2web = f"http://{public_ip}"
    print (f"Instance created ID: {instance.id}")
    print (f"Instance state: {instance.state['Name']}")

except botocore.exceptions.ClientError as error:
    print (f"Error launching instance: {error}")


######### s3 #########


#s3 resource creation
s3 = boto3.resource("s3")

#variable to bucket name randomizer 
r_dig = "".join(random.choices(string.ascii_lowercase +
                             string.digits, k=6))
r_name = "renato" + str(r_dig)

#variables containing the urls
url = "http://devops.witdemo.net/logo.jpg"
s3web = f"http://{r_name}.s3-website-us-east-1.amazonaws.com"
s3logo = f"http://{r_name}.s3.amazonaws.com/logo.jpg"

#s3 creation and error handler
try:
    response = s3.create_bucket(Bucket=r_name)
    print (f"Bucket created: {r_name}")
except botocore.exceptions.ClientError as error:
    if error.response["Error"]["Code"] == "BucketAlreadyExists":
        print (f"Bucket {r_name} already exists")
    else:
        print (f"Error creating bucket {r_Name}: {error}")

#dowloading the image and error handler
try:
    response = requests.get(url)
    response.raise_for_status()
    with open("logo.jpg", "wb") as f:
        f.write(response.content)
        print ("logo.jpg downloaded!")
except Exception as error:
    print (f"Error downloading the logo: {error}")

#uploading the image and error handler
try:
    with open("logo.jpg", "rb") as f:
        response = s3.Object(r_name, "logo.jpg").put(ACL="public-read", Body=f)
        print ("logo.jpg uploaded!")
except Exception as error:
    print (f"logo.jpg NOT uploaded: {error}")

#creating index.html for s3
with open("index.html", "w") as file:
    file.write(f"""
        <html>
        <h1>Welcome!</h1>
        <p>Done by Renato</p>
        <p>Student Number: 20099697</p>
        <img src={s3logo} alt="logo">
        </html>
    """)

#uploading index.html in s3
try:
    response = s3.Object(r_name, "index.html").put(ACL="public-read",Body=open("index.html","rb"),ContentType="")
    print ("index.html uploaded!")
except Exception as error:
    print (f"index.html NOT uploaded: {error}")

#creating error.html for s3
with open("error.html","w") as file:
    file.write(f"""
	<html>
	<h1>Error!</h1>
	<p>we had an error</p>
	</html>
    """)

#uploading error.html in s3
try:
    response = s3.Object(r_name, "error.html").put(ACL="public-read",Body=open("error.html","rb"),ContentType="")
    print ("error.html uploaded!")
except Exception as error:
    print (f"error.html NOT uploaded: {error}")

#configurating s3 if index and error
website_configuration = {
    "ErrorDocument": {"Key": "error.html"},
    "IndexDocument": {"Suffix": "index.html"},
}

bucket_website = s3.BucketWebsite(r_name)

try:
    response = bucket_website.put(WebsiteConfiguration=website_configuration)
    print ("Bucket website configured!")
except Exception as error:
    print (f"Error configuring bucket website: {error}")


######### Step 5 #########


#creating the txt file with urls
with open("renato.txt", "w") as file:
    file.write(f"EC2web link:\n{ec2web}\nS3web link:\n{s3web}")

#wait for user data to configurate ec2
print ("\nWaiting for User Data...\n")
time.sleep(160)

#opening the browser and error handler
try:
    webbrowser.get().open(ec2web)
    webbrowser.get().open(s3web)
except webbrowser.Error as error:
    print (f"Error opening web browser: {error}")


######### Step 6 #########

#command to be run
cmd1 = f"scp -o StrictHostKeyChecking=no -i my_key.pem monitor.sh ec2-user@{public_ip}:."

cmd2 = f"ssh -i my_key.pem ec2-user@{public_ip} chmod 700 monitor.sh"

cmd3 = f"ssh -i my_key.pem ec2-user@{public_ip} ./monitor.sh"

#copying monitor.sh to EC2 instance and error handler
try:
    subprocess.run(cmd1, shell=True, check=True)
except subprocess.CalledProcessError:
    print ("Error copying monitor.sh to EC2 instance")
    exit(1)

#setting execute permissions for monitor.sh and error handler
try:
    subprocess.run(cmd2, shell=True, check=True)
except subprocess.CalledProcessError:
    print ("Error setting execute permissions for monitor.sh")
    exit(1)

#running monitor.sh on EC2 instance and error handler
try:
    subprocess.run(cmd3, shell=True, check=True)
except subprocess.CalledProcessError:
    print ("Error running monitor.sh on EC2 instance")
    exit(1)


###Cloud Watch###

print ("\nMonitor Using Cloud Watch ...\n")

#enabeling cloudwatch resource
cloudwatch = boto3.resource("cloudwatch")

#enabiling cloudwatch client
cloudwatch_client = boto3.client("cloudwatch")

#enabiling SNS client
sns_client = boto3.client("sns")

try:
    # Starting iterator for CPU utilization
    cpu_metric_iterator = cloudwatch.metrics.filter(Namespace="AWS/EC2",
                                                     MetricName="CPUUtilization",
                                                     Dimensions=[{"Name":"InstanceId", "Value":instance.id}])

    # Starting iterator for Network In
    networkin_metric_iterator = cloudwatch.metrics.filter(Namespace="AWS/EC2",
                                                           MetricName="NetworkIn",
                                                           Dimensions=[{"Name":"InstanceId", "Value":instance.id}])
except Exception as error:
    print(f"Error occurred while retrieving metrics: {error}")
    exit()

#extracting first element with error handler
try:
    cpu_metric = list(cpu_metric_iterator)[0]
    networkin_metric = list(networkin_metric_iterator)[0]
except IndexError:
    print ("No matching metrics found for the specified dimensions.")
    exit()

try:
    # Creating an average statistic with 2m period for CPU utilization
    cpu_response = cpu_metric.get_statistics(StartTime=datetime.utcnow() - timedelta(minutes=5),
                                                          EndTime=datetime.utcnow(),
                                                          Period=120,
                                                          Statistics=["Minimum", "Maximum", "Average"])

    # Creating an average statistic with 2m period for Network In
    networkin_response = networkin_metric.get_statistics(StartTime=datetime.utcnow() - timedelta(minutes=5),
                                                                      EndTime=datetime.utcnow(),
                                                                      Period=120,
                                                                      Statistics=["Minimum", "Maximum", "Average"])
except botocore.exceptions.ClientError as error:
    print("An error occurred while trying to get metrics statistics:", error)
    exit()

#formating and printing the cpu data with statistics
try:
    average_cpu_utilization = cpu_response["Datapoints"][0]["Average"]
    formatted_average_cpu_utilization = f"{average_cpu_utilization:.2f}"
    print (f"Average CPU utilisation: {formatted_average_cpu_utilization}%")

    maximum_cpu_utilization = cpu_response["Datapoints"][0]["Maximum"]
    formatted_maximum_cpu_utilization = f"{maximum_cpu_utilization:.2f}"
    print (f"Maximum CPU utilisation: {formatted_maximum_cpu_utilization}%")
except (IndexError, KeyError):
    print ("No data points found for the specified time range.")
    exit()


#formating and printing the network in data with statistics
try:
    average_net_utilization = networkin_response["Datapoints"][0]["Average"]
    formatted_average_net_utilization = f"{average_net_utilization:.2f}"
    print (f"Average Incoming Traffic: {formatted_average_net_utilization}b/s")

    maximum_net_utilization = networkin_response["Datapoints"][0]["Maximum"]
    formatted_maximum_net_utilization = f"{maximum_net_utilization:.2f}"
    print (f"Maximum Incoming Traffic: {formatted_maximum_net_utilization}b/s")

    minimum_net_utilization = networkin_response["Datapoints"][0]["Minimum"]
    formatted_minimum_net_utilization = f"{minimum_net_utilization:.2f}"
    print (f"Minimum Incoming Traffic: {formatted_minimum_net_utilization}b/s")
except (IndexError, KeyError):
    print ("No data points found for the specified time range.")
    exit()

#creating SNS topic
try:
    topic_arn = sns_client.create_topic(Name="my-sns-topic")["TopicArn"]
    # Print the ARN
    print (f"Topic SNS created, topic ARN: {topic_arn}")
except Exception as error:
    print (f"Error creating topic ARN: {error}")

# setting the alarm action to send an SNS notification
try:
    cloudwatch_client.put_metric_alarm(
        AlarmName="High CPU Utilization",
        MetricName="CPUUtilization",
        Namespace="AWS/EC2" ,
        Dimensions=[{"Name":"InstanceId", "Value":instance.id}],
        Period=120,
        EvaluationPeriods=3,
        Threshold=80.0,
        ComparisonOperator="GreaterThanThreshold",
        Statistic="Average",
        AlarmDescription="This alarm will trigger when the average CPU utilization exceeds 80% for 2 minutes",
        AlarmActions=[ topic_arn ],
    )
    print("Alarm High CPU created successfully!")
except Exception as error:
    print("Error creating alarm High CPU: ", error)

# setting the alarm action to send an SNS notification and stop the EC2 instance

try:
    response = cloudwatch_client.put_metric_alarm(
        AlarmName="100 CPU Utilization",
        MetricName="CPUUtilization",
        Namespace="AWS/EC2",
        Dimensions=[{"Name": "InstanceId", "Value":instance.id}],
        Period=120,
        EvaluationPeriods=3,
        Threshold=95.0,
        ComparisonOperator="GreaterThanThreshold",
        Statistic="Average",
        AlarmActions=[ topic_arn ],
        OKActions=[
            topic_arn,
            "arn:aws:automate:us-east-1:ec2:stop",
        ],
        AlarmDescription="This alarm will trigger when the average CPU utilization exceeds 95% for 2 minutes",
    )
    print("Alarm 100 CPU created successfully!")
except Exception as error:
    print("Error creating alarm 100 CPU:", error)
