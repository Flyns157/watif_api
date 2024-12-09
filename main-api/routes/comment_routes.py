from flask import Blueprint, request, jsonify
from models.comment import Comment
from bson import ObjectId

comment_bp = Blueprint("comment_bp", __name__)

@comment_bp.route("/comments/<comment_id>", methods=["GET"])
def get_comment(comment_id):
    comment = Comment.get_by_id(ObjectId(comment_id))
    return jsonify(comment.__dict__) if comment else {"error": "Comment not found"}, 404

@comment_bp.route("/comments", methods=["POST"])
def create_comment():
    data = request.json
    comment = Comment(**data)
    comment.save()
    return jsonify(comment.__dict__), 201

@comment_bp.route("/comments/<comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    comment = Comment.get_by_id(ObjectId(comment_id))
    if comment:
        comment.delete()
        return jsonify({"message": "Comment deleted successfully"}), 200
    else:
        return jsonify({"error": "Comment not found"}), 404
