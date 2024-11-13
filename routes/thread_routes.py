from flask import Blueprint, request, jsonify
from models.thread import Thread
from bson import ObjectId

thread_bp = Blueprint("thread_bp", __name__)

@thread_bp.route("/threads/<thread_id>", methods=["GET"])
def get_thread(thread_id):
    thread = Thread.get_by_id(ObjectId(thread_id))
    return jsonify(thread.__dict__) if thread else {"error": "Thread not found"}, 404

@thread_bp.route("/threads", methods=["POST"])
def create_thread():
    data = request.json
    thread = Thread(**data)
    thread.save()
    return jsonify(thread.__dict__), 201

@thread_bp.route("/threads/<thread_id>", methods=["DELETE"])
def delete_thread(thread_id):
    thread = Thread.get_by_id(ObjectId(thread_id))
    if thread:
        thread.delete()
        return jsonify({"message": "Thread deleted successfully"}), 200
    else:
        return jsonify({"error": "Thread not found"}), 404
