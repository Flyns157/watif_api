from flask_jwt_extended import get_jwt_identity, jwt_required
from flask import Blueprint, request, jsonify
from models.thread import Thread
from bson import ObjectId
from models.user import User
from ..app import logger

thread_bp = Blueprint("thread_bp", __name__)

@thread_bp.route("/threads/<thread_id>", methods=["GET"])
@jwt_required(optional=True)
def get_thread(thread_id):
    current_user_id = get_jwt_identity()
    thread = Thread.get_by_id(ObjectId(thread_id))
    
    if thread and (thread.public or current_user_id in thread.members or current_user_id in thread.moderators):
        return jsonify(thread.__dict__), 200
    else:
        return jsonify({"error": "Thread not found or access denied"}), 404

@thread_bp.route("/threads", methods=["POST"])
@jwt_required
def create_thread():
    current_user_id = get_jwt_identity()
    try:
        data = request.get_json()
        data["id_owner"] = ObjectId(current_user_id)
        thread = Thread(**data)
        thread.save()
        return jsonify(thread.__dict__), 201
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        return jsonify({"error": "Invalid input or server error"}), 400

@thread_bp.route("/threads/<thread_id>", methods=["DELETE"])
@jwt_required
def delete_thread(thread_id):
    current_user_id = get_jwt_identity()
    current_user = User.get_by_id(current_user_id)
    thread = Thread.get_by_id(ObjectId(thread_id))

    if thread:
        if current_user_id != thread.id_owner and current_user.get_role().name != "admin":
            return jsonify({"error": "Unauthorized access"}), 403
        thread.delete()
        return jsonify({"message": "Thread deleted successfully"}), 200
    else:
        return jsonify({"error": "Thread not found"}), 404

@thread_bp.route("/threads/<thread_id>", methods=["PUT"])
@jwt_required
def update_thread(thread_id):
    current_user_id = get_jwt_identity()
    current_user = User.get_by_id(current_user_id)
    thread = Thread.get_by_id(ObjectId(thread_id))

    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    if current_user_id != thread.id_owner and current_user_id not in thread.moderators and current_user.get_role().name != "admin":
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        data = request.get_json()
        thread.update(**data)
        return jsonify(thread.__dict__), 200
    except Exception as e:
        logger.error(f"Error updating thread: {e}")
        return jsonify({"error": "Invalid input or server error"}), 400

@thread_bp.route("/threads/<thread_id>/members", methods=["POST"])
@jwt_required
def add_member(thread_id):
    current_user_id = get_jwt_identity()
    thread = Thread.get_by_id(ObjectId(thread_id))

    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    if current_user_id != thread.id_owner and current_user_id not in thread.moderators:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        data = request.get_json()
        id_user = ObjectId(data.get("id_user"))
        if thread.add_member(id_user):
            return jsonify({"message": "Member added successfully"}), 200
        else:
            return jsonify({"error": "User already a member"}), 400
    except Exception as e:
        logger.error(f"Error adding member: {e}")
        return jsonify({"error": "Invalid input or server error"}), 400

@thread_bp.route("/threads/<thread_id>/members", methods=["DELETE"])
@jwt_required
def remove_member(thread_id):
    current_user_id = get_jwt_identity()
    thread = Thread.get_by_id(ObjectId(thread_id))

    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    if current_user_id != thread.id_owner and current_user_id not in thread.moderators:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        data = request.get_json()
        id_user = ObjectId(data.get("id_user"))
        if thread.del_member(id_user):
            return jsonify({"message": "Member removed successfully"}), 200
        else:
            return jsonify({"error": "User not a member"}), 400
    except Exception as e:
        logger.error(f"Error removing member: {e}")
        return jsonify({"error": "Invalid input or server error"}), 400

@thread_bp.route("/threads/<thread_id>/moderators", methods=["POST"])
@jwt_required
def add_moderator(thread_id):
    current_user_id = get_jwt_identity()
    thread = Thread.get_by_id(ObjectId(thread_id))

    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    if current_user_id != thread.id_owner:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        data = request.get_json()
        id_user = ObjectId(data.get("id_user"))
        if thread.add_moderator(id_user):
            return jsonify({"message": "Moderator added successfully"}), 200
        else:
            return jsonify({"error": "User already a moderator"}), 400
    except Exception as e:
        logger.error(f"Error adding moderator: {e}")
        return jsonify({"error": "Invalid input or server error"}), 400

@thread_bp.route("/threads/<thread_id>/moderators", methods=["DELETE"])
@jwt_required
def remove_moderator(thread_id):
    current_user_id = get_jwt_identity()
    thread = Thread.get_by_id(ObjectId(thread_id))

    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    if current_user_id != thread.id_owner:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        data = request.get_json()
        id_user = ObjectId(data.get("id_user"))
        if thread.del_moderator(id_user):
            return jsonify({"message": "Moderator removed successfully"}), 200
        else:
            return jsonify({"error": "User not a moderator"}), 400
    except Exception as e:
        logger.error(f"Error removing moderator: {e}")
        return jsonify({"error": "Invalid input or server error"}), 400
