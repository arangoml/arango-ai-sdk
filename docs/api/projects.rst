Projects
========

You do not construct these classes yourself. The client owns a
:class:`~arango_ai_sdk.projects.ProjectManager` and exposes it as
``client.project``; its operations return
:class:`~arango_ai_sdk.projects.AIProject` instances.

.. autoclass:: arango_ai_sdk.projects.ProjectManager
   :members: create

.. autoclass:: arango_ai_sdk.projects.AIProject
   :members:
