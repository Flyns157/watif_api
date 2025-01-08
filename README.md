# Maquette d'une API RESTful en Python avec FastAPI

Ce projet est un projet de maquettage d'une API RESTful en Python avec FastAPI scalable verticalement et horizontalement doublé d'une facilité d'utilisation.

## Structure du projet

```
└── 📁watif
    └── 📁app
        └── __init__.py
        └── __main__.py
        └── 📁data
            └── 📁databases
                └── __init__.py
                └── mongodb.py
                └── neo4j.py
                └── synchronizer.py
            └── 📁models
                └── __init__.py
                └── .models.puml
                └── interest.py
                └── key.py
                └── post.py
                └── role.py
                └── thread.py
                └── token.py
                └── user.py
            └── 📁transactions
                └── 📁mongodb
                    └── __init__.py
                └── 📁neo4j
                    └── __init__.py
                └── user.py
        └── 📁routers
            └── __init__.py
            └── auth.py
            └── em_router.py
            └── ja_router.py
            └── mc_router.py
            └── post.py
            └── thread.py
            └── user.py
        └── 📁security
            └── auth.py
            └── security.conf
        └── 📁services
            └── 📁ImgGen
                └── genimg.conf
            └── 📁Recommender
                └── __init__.py
                └── em_engine.py
                └── 📁embedding
                    └── __init__.py
                    └── mc_core.py
                └── ja_engine.py
                └── mc_engine.py
                └── README.md
                └── recommender.conf
        └── 📁utils
            └── __init__.py
            └── 📁config
                └── __init__.py
                └── main.conf
                └── modes.py
            └── exceptions.py
    └── 📁docker
        └── Dockerfile.dev
        └── Dockerfile.prod
        └── init-mongo.js
    └── 📁storage
        └── 📁images
        └── 📁pp
            └── default-avatar-icon-of-social-media-user-vector.jpg
    └── 📁tests
        └── __main__.py
        └── main.py
        └── test.py
    └── .dockerignore
    └── .env
    └── .env.example
    └── .gitignore
    └── docker-compose.yml
    └── gitlab-ci.yml
    └── LICENCE
    └── README.md
    └── requirements.in
    └── setup.py
```
