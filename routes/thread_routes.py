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
    
    if thread and (thread.public or current_user_id in thread.members):
        return jsonify(thread.__dict__), 200
    else:
        return jsonify({"error": "Thread not found"}), 404

@thread_bp.route("/threads", methods=["POST"])
@jwt_required
def create_thread():
    current_user_id = get_jwt_identity()
    
    # Gestion des erreurs pour le format de la donnée reçue
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            logger.error(f"Invalid input format - Expected a JSON object")
            return jsonify({"error": "Invalid input format; expected a JSON object"}), 400
    except Exception:
        logger.error(f"Invalid JSON input")
        return jsonify({"error": "Invalid JSON input"}), 400

    data["id_owner"] = current_user_id
    try:
        thread = Thread(**data)
        thread.save()
        return jsonify(thread.__dict__), 201
    except Exception as e:
        logger.error(f"Invalid JSON input ({data}) causing issue : {e}")
        return jsonify({"error": "Invalid JSON input"}), 400

@thread_bp.route("/threads/<thread_id>", methods=["DELETE"])
@jwt_required
def delete_thread(thread_id):
    current_user_id = get_jwt_identity()
    current_user = User.get_by_id(current_user_id)
    logger.info(f"DELETE /threads/{thread_id} - Current user ID: {current_user_id}")
    thread = Thread.get_by_id(ObjectId(thread_id))

    if thread:
        # Autoriser uniquement l'utilisateur ou un administrateur
        if current_user_id != thread.id_owner and current_user.get_role().name != 'admin':
            logger.error(f"Unauthorized access - User ID: {current_user_id} - to delete Thread: {thread_id}")
            return jsonify({"error": "Unauthorized access"}), 403

        thread.delete()
        logger.info(f"Thread {thread_id} deleted successfully")
        return jsonify({"message": "User deleted successfully"}), 200
    else:
        logger.error(f"Thread {thread_id} not found")
        return jsonify({"error": "User not found"}), 404
