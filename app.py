from flask import Flask, request, jsonify, render_template
import boto3
from decimal import Decimal

app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('StudentsNoSQL')

def clean(item):
    return {k: (float(v) if isinstance(v, Decimal) else v) for k, v in item.items()}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/students', methods=['POST'])
def create_student():
    data = request.json
    table.put_item(Item={
        'student_id': data['student_id'],
        'name': data['name'],
        'age': Decimal(str(data['age'])),
        'is_active': data.get('is_active', True),
        'subjects': data.get('subjects', []),
        'address': data.get('address', {})
    })
    return jsonify({'message': 'Student created'}), 201

@app.route('/students', methods=['GET'])
def get_all_students():
    response = table.scan()
    return jsonify([clean(i) for i in response['Items']])

@app.route('/students/<student_id>', methods=['GET'])
def get_student(student_id):
    response = table.get_item(Key={'student_id': student_id})
    item = response.get('Item')
    return jsonify(clean(item)) if item else (jsonify({'error':'Not found'}), 404)

@app.route('/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    data = request.json
    table.update_item(
        Key={'student_id': student_id},
        UpdateExpression="SET #n = :n, age = :a, is_active = :ia, subjects = :s, address = :addr",
        ExpressionAttributeNames={'#n': 'name'},
        ExpressionAttributeValues={
            ':n': data['name'],
            ':a': Decimal(str(data['age'])),
            ':ia': data.get('is_active', True),
            ':s': data.get('subjects', []),
            ':addr': data.get('address', {})
        }
    )
    return jsonify({'message': 'Student updated'})

@app.route('/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    table.delete_item(Key={'student_id': student_id})
    return jsonify({'message': 'Student deleted'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
