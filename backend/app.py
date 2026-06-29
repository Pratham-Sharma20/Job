from flask import Flask, jsonify
from flask_cors import CORS
from db import jobs_collection
from pymongo.errors import PyMongoError

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Job scraper backend is running"
    })

@app.route("/jobs", methods=["GET"])
def get_jobs():
    try:
        jobs = list(jobs_collection.find({}, {"_id": 0}))
        return jsonify(jobs)
    except PyMongoError as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500

from scheduler import start_scheduler_thread

if __name__ == "__main__":
    start_scheduler_thread()
    app.run(debug=True, port=5000)