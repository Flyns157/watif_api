from bson import ObjectId

def isobjectid(obj: object) -> bool:
    try:
        ObjectId(obj)
        return True
    except:
        return False
