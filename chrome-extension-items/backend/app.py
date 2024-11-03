from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

@app.route('/generate_schedule', methods=['POST'])
def generate_schedule():
    data = request.json
    calendar_content = data.get('calendarContent')
    health_content = data.get('healthContent')
    date = data.get('date')

    # Here, you would implement your logic to generate a schedule
    # For demonstration, we will just return the received data
    schedule = {
        'calendar': calendar_content,
        'health': health_content,
        'date': date,
        'message': 'Schedule generated successfully!'
    }
    
    return jsonify(schedule)

if __name__ == '__main__':
    app.run(debug=True)