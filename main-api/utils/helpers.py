from bson import ObjectId

def isobjectid(obj: object) -> bool:
    try:
        ObjectId(obj)
        return True
    except:
        return False

def allowed_file(filename: str) -> bool:
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
