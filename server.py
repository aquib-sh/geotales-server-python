import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, OperationFailure
from datetime import datetime
import os
import base64


app = Flask(__name__)
CORS(app)


mongo_url = os.environ["MONGODB_URI"]
client = MongoClient(mongo_url)
db = client.get_database("geotales")
image_collection = db["images"]


@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files['image']
    data = request.form
    image_content = file.read()
    base64_image = base64.b64encode(image_content).decode("utf-8")

    new_image = {
        "id": data["id"],
        "userId": data["userId"],
        "userEmail": data["userEmail"],
        "fileName": data["fileName"],
        "fileType": data["fileType"],
        "latitude": float(data["latitude"]),
        "longitude": float(data["longitude"]),
        "uploadTimestamp": time.time(),       
        "imageContent": base64_image
    }

    try:
        image_collection.insert_one(new_image)
        return jsonify({"message": "Image uploaded successfully"})
    except Exception as err:
        print(err)
        return jsonify({"error": "Failed to save image"}), 500


def convert_objectid_to_string(image):
    image['_id'] = str(image['_id'])
    image['uploadTimestamp'] = datetime.utcfromtimestamp(image['uploadTimestamp']).isoformat()
    return image


@app.route('/images', methods=['GET'])
def get_all_images():
    images = list(image_collection.find())
    images = [convert_objectid_to_string(image) for image in images]
    return jsonify(images)


@app.route('/images/location/<latitude>/<longitude>', methods=['GET'])
def get_images_by_location(latitude, longitude):
    images = list(image_collection.find({"latitude": float(latitude), "longitude": float(longitude)}))
    return jsonify(images)

@app.route('/images/user/<userId>', methods=['GET'])
def get_images_by_user(userId):
    images = list(image_collection.find({"userId": userId}))
    return jsonify(images)

@app.route('/images_info', methods=['GET'])
def get_images_info():
    images = list(image_collection.find({}, {"imageContent": 0}))
    return jsonify(images)


@app.route('/images/id/<image_id>', methods=['GET'])
def get_image_by_id(image_id):
    image = image_collection.find_one({"id": image_id})
    if image:
        return jsonify(image)
    else:
        return jsonify({"error": "Image not found"}), 404


@app.route('/coordinates', methods=['GET'])
def get_coordinates():
    coordinates = list(image_collection.find({}, {"_id": 0, "latitude": 1, "longitude": 1}))
    return jsonify(coordinates), 200



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)

