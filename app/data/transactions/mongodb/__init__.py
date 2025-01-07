from importlib import import_module
from pymongo import ReturnDocument
import inflect
import inspect

from ...models import PyUUID
from .... import mongodb


inflector = inflect.engine()


class BaseModelCRUD:
    @classmethod
    def _get_collection_name(cls):
        """
        Convertit le nom de la classe en nom de collection (ex. : Thread -> threads).
        """
        return inflector.plural(cls.__name__.lower())

    @classmethod
    def _get_update_model(cls):
        """
        Importe dynamiquement le modèle de mise à jour correspondant à la classe.
        Lève une exception si le modèle d'update n'existe pas.
        """
        module_path = f"..models.{cls.__name__.lower()}"
        update_model_name = f"{cls.__name__}Update"
        try:
            module = import_module(module_path, package=__package__)
            return getattr(module, update_model_name)
        except (ModuleNotFoundError, AttributeError):
            raise NotImplementedError(
                f"{cls.__name__} does not support updates because "
                f"the update model '{update_model_name}' could not be found."
            )

    @classmethod
    async def _retrieve(cls, uuid: PyUUID):
        """
        Récupère un document dans la base MongoDB à partir de son UUID.
        """
        collection_name = cls._get_collection_name()
        document = await mongodb.db[collection_name].find_one({"uuid": str(uuid)})
        if document:
            return cls(**document)

    async def _create(self):
        """
        Crée un nouveau document dans la base MongoDB.
        """
        collection_name = self._get_collection_name()
        return await mongodb.db[collection_name].insert_one(self.model_dump())

    async def _update(self):
        """
        Met à jour un document existant dans la base MongoDB.
        """
        collection_name = self._get_collection_name()
        update_model = self._get_update_model()
        return await mongodb.db[collection_name].find_one_and_update(
            {"uuid": str(self.uuid)},
            {"$set": update_model(**self.model_dump())},
            return_document=ReturnDocument.AFTER,
        )

    async def _save(self):
        """
        Sauvegarde un document (création ou mise à jour selon l'existence).
        """
        collection_name = self._get_collection_name()
        existing = await mongodb.db[collection_name].find_one({"uuid": str(self.uuid)})
        if existing:
            return await self._update()
        return await self._create()

    async def _delete(self):
        """
        Supprime un document de la base MongoDB.
        """
        collection_name = self._get_collection_name()
        return await mongodb.db[collection_name].delete_one({"uuid": str(self.uuid)})


def list_model_classes(module):
    """
    Liste les classes d'un module dont le nom se termine par 'Model'.
    
    Args:
        module: Le module Python à analyser.
        
    Returns:
        list: Une liste de classes dont le nom se termine par 'Model'.
    """
    return [
        cls
        for name, cls in inspect.getmembers(module, inspect.isclass)
        if name.endswith("Model") and cls.__module__ == module.__name__
    ]


def generate_crud_classes(base_module, excluded_files=None):
    """
    Génère dynamiquement une classe intégrant BaseModelCRUD 
    pour chaque classe 'Model' contenue dans un module donné,
    sauf si elle est définie dans un fichier exclu.

    Args:
        base_module: Le module contenant les classes 'Model'.
        excluded_files: Liste de fichiers (avec chemin absolu ou relatif)
                        contenant les classes à exclure.

    Returns:
        dict: Un dictionnaire des nouvelles classes CRUD générées.
              La clé est le nom de la classe, la valeur est la classe elle-même.
    """
    if excluded_files is None:
        excluded_files = []

    # Convertit les chemins exclus en absolu pour des comparaisons cohérentes
    excluded_files = {inspect.getfile(import_module(f)).lower() for f in excluded_files}
    
    crud_classes = {}

    for name, cls in inspect.getmembers(base_module, inspect.isclass):
        # Vérifie si la classe se termine par 'Model' et provient du module donné
        if name.endswith("Model") and cls.__module__ == base_module.__name__:
            # Vérifie si la classe est définie dans un fichier exclu
            # TODO : automatiser la détection de l'existance de la classe dans un autre fichier plutot que de le faire manuellement
            source_file = inspect.getfile(cls).lower()
            if source_file not in excluded_files:
                # Génère une nouvelle classe CRUD
                crud_class_name = name[:-5]  # Supprime 'Model' du nom
                crud_class = type(
                    crud_class_name,  # Nom de la classe
                    (cls, BaseModelCRUD),  # Hérite de la classe modèle et de BaseModelCRUD
                    {}  # Pas d'attributs supplémentaires pour le moment
                )
                crud_classes[crud_class_name] = crud_class

    return crud_classes


# Génération des classes CRUD
try:
    from ... import models  # Remplacez par le chemin réel du module
    generated_classes = generate_crud_classes(
        models,
        excluded_files=[]
    )

    # Attacher les classes générées à l'espace de noms actuel
    globals().update(generated_classes)

except ModuleNotFoundError as e:
    raise ImportError(f"Impossible d'importer le module de modèles : {e}")
