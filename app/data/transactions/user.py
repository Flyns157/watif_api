from . import BaseModelCRUD
from ..models import PostModel
from ... import mongodb

class Post(PostModel, BaseModelCRUD):

    async def _create(self):
        # Exemple of how to create a post with a special logic
        super()._create()