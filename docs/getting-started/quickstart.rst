.. _quickstart:

Quickstart
==========

This page walks through everything the SDK offers today: connect to your
deployment and create a project. Later areas (files, ingestion, retrieval) will
extend this same script.

You need:

- the endpoint of your Arango deployment, including the port, exactly as the
  deployment publishes it, for example ``https://<your-deployment>:8529``;
- a username and password that can access the database you want to work in.

Create a client and a project
-----------------------------

.. code-block:: python

   from arango_ai_sdk import ArangoAIClient

   client = ArangoAIClient(
       base_url="https://<your-deployment>:8529",
       project_name="my_first_project",
       username="<username>",
       password="<password>",
   )

   try:
       project = client.project.create(
           project_name="my_first_project",
           project_type="autograph",
           description="Created from the quickstart.",
       )
       print(project.project_name, project.project_type, project.project_db_name)
   finally:
       client.close()

What happened
-------------

1. Constructing :class:`~arango_ai_sdk.ArangoAIClient` signed you in. The SDK
   exchanged the credentials for a token, checked that the database exists, and
   keeps the token in memory for the client's lifetime. Wrong credentials or a
   misspelt database fail here, not on the first real call. See
   :ref:`authentication`.

2. ``client.project.create(...)`` created the project and returned it as an
   :class:`~arango_ai_sdk.models.AiProject`. See :ref:`projects-create`.

3. ``client.close()`` released the network connections. It is safe to call more
   than once.

Every exception the SDK raises descends from
:exc:`~arango_ai_sdk.exceptions.ArangoAIError`, so one ``except`` clause is
enough to catch anything the SDK can raise. See :ref:`errors`.

What comes next
---------------

Once the remaining areas ship, the same client will upload documents into the
project, build the context graph from them, and answer questions against it.
