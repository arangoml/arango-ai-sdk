arango-ai-sdk
=============

``arango-ai-sdk`` is the Python SDK for the Arango AI Suite. It is the code-first way
to drive an AutoGraph workflow: authenticate, create a project, store the API keys
it needs, upload documents, build the context graph, and ask questions against it. You never assemble a URL,
set an authentication header, poll a job by hand, or interpret an HTTP status code.
The SDK does that and raises a named exception when something goes wrong.

The SDK is organised in areas, and each area is a namespace on the client:

.. list-table::
   :header-rows: 1
   :widths: 22 48 30

   * - Area
     - What it covers
     - Status
   * - Authentication
     - Sign in once with a username and password; every later call is authenticated for you.
     - Available
   * - Projects (``client.project``)
     - The project everything else happens in.
     - Available: create
   * - Secret profiles (``client.secret_profile``)
     - Store a provider API key once; later stages refer to it by ID.
     - Available: create, get
   * - Files
     - Upload the documents to ingest.
     - Planned
   * - Ingestion
     - Build the context graph from the uploaded documents.
     - Planned
   * - Retrieval
     - Ask questions against the built context graph.
     - Planned

.. note::

   The SDK is pre-alpha and grows one area at a time. This documentation covers
   what is available today; planned areas are listed above so you know what is
   coming, but they have no pages yet.

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   getting-started/index

.. toctree::
   :maxdepth: 2
   :caption: Using the SDK

   client/index
   projects/index
   secret-profiles/index
   errors/index

.. toctree::
   :maxdepth: 2
   :caption: Reference

   api/index
