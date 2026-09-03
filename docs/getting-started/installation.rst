.. _installation:

Installation
============

``arango-ai-sdk`` requires Python 3.12 or newer.

The package is currently published to ArangoDB's **private** package index
(Google Artifact Registry). Availability on the public PyPI is a later step.

Authenticate to the registry
----------------------------

The registry uses Google Artifact Registry keyring support:

.. code-block:: bash

   pip install keyring keyrings.google-artifactregistry-auth
   gcloud auth login   # or supply a service-account key

Install with pip
----------------

.. code-block:: bash

   pip install arango-ai-sdk \
     --extra-index-url https://europe-west3-python.pkg.dev/arango-ml/arango-ml-internal-pypi/simple/

Install with uv
---------------

Declare the index in the consuming project's ``pyproject.toml``:

.. code-block:: toml

   [[tool.uv.index]]
   name = "arango_private"
   url = "https://europe-west3-python.pkg.dev/arango-ml/arango-ml-internal-pypi/simple/"
   explicit = true

   [tool.uv.sources]
   arango-ai-sdk = { index = "arango_private" }

Then add the dependency:

.. code-block:: bash

   uv add arango-ai-sdk

Verify the installation
-----------------------

.. code-block:: python

   import arango_ai_sdk

   print(arango_ai_sdk.__version__)
