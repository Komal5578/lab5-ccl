# Lab 5 – DynamoDB CRUD App

## Table Details
- Table name: StudentsNoSQL
- Partition key: student_id (String)
- Region: ap-south-1 (Asia Pacific - Mumbai)

## IAM Role
- Role name: EC2-DynamoDB-Role
- Policy attached: AmazonDynamoDBFullAccess
- Used for secure access from EC2 to DynamoDB (no hardcoded AWS keys)

## How to Run
1. SSH into the EC2 instance
2. cd ~/dynamo-app
3. source venv/bin/activate
4. python3 app.py

## App URL Format
http://<EC2-Public-IP>:5000
