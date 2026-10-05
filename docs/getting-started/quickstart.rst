.. _quickstart:

Quickstart
==========

This page walks through the first three steps of every SDK script: connect to
your deployment, create a project and create a secret profile. Uploading files,
deploying AutoGraph and ingesting extend this same script; the end of the page
points to them.

You need:

- the endpoint of your Arango deployment, including the port, exactly as the
  deployment publishes it, for example ``https://<your-deployment>:8529``;
- a username and password that can access the database you want to work in;
- an API key for the model provider you want AutoGraph to use, for example an
  OpenAI key.

Create a client, a project and a secret profile
-----------------------------------------------

.. code-block:: python

   from arango_ai_sdk import ArangoAIClient

   client = ArangoAIClient(
       base_url="https://<your-deployment>:8529",
       username="<username>",
       password="<password>",
   )

   try:
       project = client.project.create(
           project_name="my_first_project",
           project_type="autograph",
           description="Created from the quickstart.",
       )
       print(project.name, project.project_type, project.db_name)

       profile = client.secret_profile.create(
           name="openai-quickstart",
           secret="<your-api-key>",
           provider="openai",
           description="Created from the quickstart.",
       )
       print(profile.profile_id, profile.name, profile.profile_type)
   finally:
       client.close()

What happened
-------------

1. Constructing :class:`~arango_ai_sdk.ArangoAIClient` signed you in. The SDK
   exchanged the credentials for a token, checked that the database exists, and
   keeps the token in memory for the client's lifetime. Wrong credentials or a
   misspelt database fail here, not on the first real call. See
   :ref:`authentication`.

2. ``client.project.create(...)`` created the project and returned an
   :class:`~arango_ai_sdk.AiProjectHandle` bound to it. The handle is where
   everything project-scoped happens; the client itself is not tied to any
   project. See :ref:`projects-create`.

3. ``client.secret_profile.create(...)`` stored the API key encrypted on the
   platform and returned it as a :class:`~arango_ai_sdk.models.Profile`. Keep
   ``profile.profile_id``: later stages refer to the key by that ID and never
   see the key itself. See :ref:`secret-profiles-create`.

4. ``client.close()`` released the network connections. It is safe to call more
   than once.

Every exception the SDK raises descends from
:exc:`~arango_ai_sdk.exceptions.ArangoAIError`, so one ``except`` clause is
enough to catch anything the SDK can raise. See :ref:`errors`.

What comes next
---------------

The rest of the pipeline continues from the ``project`` handle and the
``profile`` ID this script created:

1. Upload the documents under the project's categories with
   ``client.files.upload_folder(...)``. See :ref:`files`.
2. Deploy AutoGraph into the project with ``project.autograph.deploy(...)``,
   passing the profile ID for the chat and embedding models. See
   :ref:`autograph-deploy`.
3. Build the context graph with ``project.autograph.ingest(...)``. See
   :ref:`autograph-ingest`. The same work is also available as separate
   steps: :ref:`autograph-corpus-build`, :ref:`autograph-strategize`,
   :ref:`autograph-strategies` and :ref:`autograph-orchestrate`.

A notebook that runs the whole flow against a sample corpus, from sign-in to
``ingest`` and clean-up, ships in the repository under
``examples/sdk-demo/AI_Suite_SDK_demo.ipynb``.

Retrieval, asking questions against the built graph, is not available yet.
