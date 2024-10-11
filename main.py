from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, origins='*')

# API placeholder
@app.route("/api/users", methods=["GET"])
def users():
    return jsonify(
        {
            "users": [
                'Alice', 'Bob', 'Charlie', 'David', 'Eve'
            ]
        }
    )

if __name__ == "__main__":
    app.run(debug=True, port=8080)