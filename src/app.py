"""
Main Flask application - Calculator Backend API.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.expression_parser import ExpressionParser, ExpressionError
from model.database import init_db, add_record, get_all_records, delete_record, clear_all_records

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend separation

parser = ExpressionParser()


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculate a mathematical expression."""
    data = request.get_json()

    if not data or 'expression' not in data:
        return jsonify({
            'success': False,
            'message': 'Missing expression in request body'
        }), 400

    expression = data['expression'].strip()

    try:
        result = parser.calculate(expression)
        result_str = str(result)

        # Save to history
        add_record(expression, result_str)

        return jsonify({
            'success': True,
            'expression': expression,
            'result': result
        }), 200

    except ExpressionError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal error: {str(e)}'
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get all calculation history records."""
    try:
        records = get_all_records()
        return jsonify({
            'success': True,
            'data': records
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/history/<int:record_id>', methods=['DELETE'])
def delete_history(record_id):
    """Delete a specific history record by ID."""
    try:
        deleted = delete_record(record_id)
        if deleted:
            return jsonify({
                'success': True,
                'message': f'Record {record_id} deleted'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Record {record_id} not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """Clear all calculation history (extended feature)."""
    try:
        count = clear_all_records()
        return jsonify({
            'success': True,
            'message': f'Cleared {count} records'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    init_db()
    print("Calculator Backend Server starting on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
