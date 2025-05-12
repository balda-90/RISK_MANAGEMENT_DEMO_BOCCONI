from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Load risk data
def load_risk_data():
    try:
        with open('data/risk_assessment_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save risk data
def save_risk_data(data):
    Path("data").mkdir(exist_ok=True)
    with open('data/risk_assessment_data.json', 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/api/risks', methods=['GET'])
def get_risks():
    risks = load_risk_data()
    return jsonify(risks)

@app.route('/api/risks', methods=['POST'])
def add_risk():
    risks = load_risk_data()
    new_risk = request.json
    risks.append(new_risk)
    save_risk_data(risks)
    return jsonify({"message": "Risk added successfully", "risk": new_risk})

@app.route('/api/risks/<risk_id>', methods=['PUT'])
def update_risk(risk_id):
    risks = load_risk_data()
    updated_risk = request.json
    
    for i, risk in enumerate(risks):
        if risk.get('Risk_ID') == risk_id:
            risks[i] = updated_risk
            save_risk_data(risks)
            return jsonify({"message": "Risk updated successfully", "risk": updated_risk})
    
    return jsonify({"error": "Risk not found"}), 404

@app.route('/api/risks/<risk_id>', methods=['DELETE'])
def delete_risk(risk_id):
    risks = load_risk_data()
    
    for i, risk in enumerate(risks):
        if risk.get('Risk_ID') == risk_id:
            deleted_risk = risks.pop(i)
            save_risk_data(risks)
            return jsonify({"message": "Risk deleted successfully", "risk": deleted_risk})
    
    return jsonify({"error": "Risk not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000) 