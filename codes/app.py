from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for frontend communication

# MongoDB Atlas Connection
MONGODB_URI = os.getenv('MONGODB_URI', 'your_mongodb_connection_string_here')
client = MongoClient(MONGODB_URI)
db = client['student_biodata_db']
students_collection = db['students']

# Serve HTML frontend pages
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/index.html')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/add.html')
def serve_add():
    return app.send_static_file('add.html')

@app.route('/view.html')
def serve_view():
    return app.send_static_file('view.html')

@app.route('/edit.html')
def serve_edit():
    return app.send_static_file('edit.html')

@app.route('/delete.html')
def serve_delete():
    return app.send_static_file('delete.html')

# API Routes

@app.route('/api/students', methods=['POST'])
def add_student():
    """Add new student"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'college', 'father', 'mother', 'marks10', 'marks12', 'school10', 'school12']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if student already exists
        existing = students_collection.find_one({'name': data['name']})
        if existing:
            return jsonify({'error': f"Student with name '{data['name']}' already exists"}), 409
        
        # Insert student data
        student = {
            'name': data['name'],
            'college': data['college'],
            'father': data['father'],
            'mother': data['mother'],
            'marks10': float(data['marks10']),
            'marks12': float(data['marks12']),
            'school10': data['school10'],
            'school12': data['school12']
        }
        
        result = students_collection.insert_one(student)
        
        return jsonify({
            'message': f"Biodata saved successfully for {data['name']}!",
            'id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<name>', methods=['GET'])
def get_student(name):
    """Get student by name"""
    try:
        student = students_collection.find_one({'name': name})
        
        if not student:
            return jsonify({'error': f"No biodata found for '{name}'"}), 404
        
        # Convert ObjectId to string
        student['_id'] = str(student['_id'])
        
        return jsonify(student), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/college/<college_name>', methods=['GET'])
def get_students_by_college(college_name):
    """Get all students from a specific college"""
    try:
        # Case-insensitive search
        students = list(students_collection.find({'college': {'$regex': f'^{college_name}$', '$options': 'i'}}))
        
        # Convert ObjectId to string for all students
        for student in students:
            student['_id'] = str(student['_id'])
        
        return jsonify(students), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<old_name>', methods=['PUT'])
def update_student(old_name):
    """Update student data"""
    try:
        data = request.json
        
        # Find existing student
        existing = students_collection.find_one({'name': old_name})
        if not existing:
            return jsonify({'error': f"No biodata found for '{old_name}'"}), 404
        
        # Prepare update data
        update_data = {
            'name': data.get('name', old_name),
            'college': data['college'],
            'father': data['father'],
            'mother': data['mother'],
            'marks10': float(data['marks10']),
            'marks12': float(data['marks12']),
            'school10': data['school10'],
            'school12': data['school12']
        }
        
        # If name changed, check if new name already exists
        if update_data['name'] != old_name:
            name_exists = students_collection.find_one({'name': update_data['name']})
            if name_exists:
                return jsonify({'error': f"Student with name '{update_data['name']}' already exists"}), 409
        
        # Update student
        students_collection.update_one(
            {'name': old_name},
            {'$set': update_data}
        )
        
        return jsonify({'message': 'Biodata updated successfully!'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<name>', methods=['DELETE'])
def delete_student(name):
    """Delete student data"""
    try:
        result = students_collection.delete_one({'name': name})
        
        if result.deleted_count == 0:
            return jsonify({'error': f"No biodata found for '{name}'"}), 404
        
        return jsonify({'message': f"Biodata for '{name}' deleted successfully!"}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_all_students():
    """Get all students (optional - for listing)"""
    try:
        students = list(students_collection.find())
        
        # Convert ObjectId to string
        for student in students:
            student['_id'] = str(student['_id'])
        
        return jsonify(students), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if API and database are working"""
    try:
        # Ping database
        client.admin.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # For development
    app.run(debug=True, host='0.0.0.0', port=5000)
