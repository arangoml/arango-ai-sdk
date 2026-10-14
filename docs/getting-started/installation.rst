.. _installation:

Installation
============

``arango-ai-sdk`` requires Python 3.12 or newer.

**Status: work in progress.** Install from a checkout of this repository.
Publishing to the public PyPI is a later step.

Install from a checkout
-----------------------

Install `uv <https://docs.astral.sh/uv/>`_, then:

.. code-block:: bash

   git clone https://github.com/arangoml/arango-ai-sdk
   cd arango-ai-sdk
   make install

``make install`` runs ``uv sync`` and creates ``.venv``. Without ``make``, as
on a default Windows setup, run ``uv sync`` directly. Activate the environment
before running a script that imports the SDK:

.. code-block:: bash

   source .venv/bin/activate          # macOS and Linux
   .venv\Scripts\activate             # Windows

The private package index
-------------------------

The package is also published to ArangoDB's **private** package index
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
