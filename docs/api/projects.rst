Projects
========

You do not construct these classes yourself. The client owns a
:class:`~arango_ai_sdk.managers.projects.ProjectManager` and exposes it as
``client.project``. Its operations return
:class:`~arango_ai_sdk.AiProjectHandle` instances, each bound to one project
and sharing the client's connection. The handle wraps the raw
:class:`~arango_ai_sdk.models.AiProject` record, documented in :doc:`models`.

.. autoclass:: arango_ai_sdk.managers.projects.ProjectManager
   :members: create, get

.. autoclass:: arango_ai_sdk.AiProjectHandle
   :members:
