from flask import Blueprint, request, jsonify
from models.post import Post
from bson import ObjectId

post_bp = Blueprint("post_bp", __name__)

@post_bp.route("/posts/<post_id>", methods=["GET"])
def get_post(post_id):
    post = Post.get_by_id(ObjectId(post_id))
    return jsonify(post.__dict__) if post else {"error": "Post not found"}, 404

@post_bp.route("/posts", methods=["POST"])
def create_post():
    data = request.json
    post = Post(**data)
    post.save()
    return jsonify(post.__dict__), 201

@post_bp.route("/posts/<post_id>", methods=["DELETE"])
def delete_post(post_id):
    post = Post.get_by_id(ObjectId(post_id))
    if post:
        post.delete()
        return jsonify({"message": "Post deleted successfully"}), 200
    else:
        return jsonify({"error": "Post not found"}), 404
