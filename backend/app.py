import os
from flask import Flask, jsonify
from flask_cors import CORS
from db import jobs_collection
from pymongo.errors import PyMongoError
from scheduler import start_scheduler_thread

app = Flask(__name__)
CORS(app)

start_scheduler_thread()

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
        return jsonify({
            "error": "Database error",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )