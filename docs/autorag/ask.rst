.. _autorag-ask:

Asking a question
=================

.. code-block:: python

   from arango_ai_sdk.models import QueryType

   answer = retriever.ask(
       "What do the contracts say about renewal?",
       query_type=QueryType.UNIFIED,
   )
   print(answer.run_id)
   print(answer.result)

One call sends one question to this retriever and returns the answer. You do
not choose an endpoint or a query mode by string. The retriever must already
be deployed and serving; see :ref:`autorag-deploy`.

``ask`` reloads the project first and refuses, before anything is sent, when
this retriever is no longer listed there.

Parameters
----------

.. list-table::
   :header-rows: 1
   :widths: 28 24 48

   * - Parameter
     - Type
     - Meaning
   * - ``query``
     - ``str``
     - The question, in natural language. Required. A blank string is
       rejected and nothing is sent.
   * - ``query_type``
     - :class:`~arango_ai_sdk.models.QueryType`
     - How the retriever searches. Default ``UNIFIED``.
   * - ``response_instructions``
     - ``str``, optional
     - Style instructions for the answer, such as ``"Short answer"``.
       Omitted leaves the service's own default.
   * - ``include_metadata``
     - ``bool``
     - Whether the response includes retrieval metadata. Default ``False``.
   * - ``partition_ids``
     - sequence of ``str``, optional
     - Restrict retrieval to these partitions. Omitted lets the service
       choose the relevant partitions itself.
   * - ``show_citations``
     - ``bool``, optional
     - Whether to keep inline citations in the answer. Omitted leaves the
       service default, which keeps them.
   * - ``model``
     - ``str``, optional
     - Chat model for this question only, instead of the model stored at
       deploy. The embedding model is unchanged.

How the retriever searches
--------------------------

``query_type`` is a :class:`~arango_ai_sdk.models.QueryType`, not a string.

``QueryType.LOCAL``
   Starts from the people, companies and other entities named in the question
   and follows their relationships. Fits a specific fact.

``QueryType.GLOBAL``
   Reads the summaries of each part of the graph. Fits a question about
   themes across the whole corpus. It needs full-graph partitions. On a
   partition that is vectors only, the service cannot answer this way.

``QueryType.UNIFIED``
   Combines matching text passages with the graph. This is the default, and
   it works on both vectors-only partitions and full-graph partitions. Use it
   when you are not sure which of the other two fits.

``QueryType.CUSTOM`` is a value the service defines. ``ask`` will send it,
but the SDK does not take the custom-tool arguments that mode needs, so
leave it unset.

The service's own default, if you never chose a mode, would be global. The
SDK does not leave it unset: omitting ``query_type`` sends ``UNIFIED``, so a
project whose clusters are vectors only still answers.

What ``ask`` does not take
--------------------------

The retriever service can plan a question across several hops
(``use_llm_planner``) and can stream the answer. Neither is a parameter of
``ask``. A question is one request and one complete answer. To change how
much of the corpus becomes a full graph, set ``complexity`` when you
:ref:`ingest <autograph-ingest>` or :ref:`strategize <autograph-strategize>`,
not when you ask.

Return value
------------

A :class:`~arango_ai_sdk.models.GraphRagQueryResponse`.

``result``
   The answer text.

``run_id``
   The id of this query as the platform stored it. Keep it if you need to
   point at this answer later. The SDK cannot list past runs.

``metadata``
   Extra retrieval detail, only when you passed ``include_metadata=True``.
   Otherwise it is empty. It is a string, not a parsed object.

A response the service completed with a non-empty ``error_code`` is not
returned. ``ask`` raises instead, so a failed question never looks like an
empty ``result``.

Errors
------

:exc:`ValueError`
   ``query`` is empty or only whitespace. Nothing was sent.

:exc:`~arango_ai_sdk.exceptions.AutoRagNotDeployedError`
   This retriever is no longer in the project, so nothing was sent. ``ask``
   also raises it when the query endpoint answers ``404``, which right after
   a deploy can be the gateway still registering the route; call
   ``wait_until_ready`` before the first question.

:exc:`~arango_ai_sdk.exceptions.QueryFailedError`
   The service answered, including with HTTP 200, but the body carried a
   failure code instead of an answer. ``failure_code`` is that code, for
   example ``INSUFFICIENT_QUOTA`` or ``INVALID_API_KEY``. ``run_id`` is the
   stored run, or empty when the service stored none. ``status_code`` is 200
   for this case: the call reached the retriever and the retriever reported
   the failure in the body.

A global question against a vectors-only partition has no communities to read.
The retriever then returns that as a normal answer, with ``result`` set to
``"No communities found at the specified level."`` It does not raise.
``QueryFailedError`` is a non-empty ``error_code`` on the response.

Any other failure surfaces as one of the general SDK exceptions described in
:ref:`errors`.

Example
-------

.. code-block:: python

   from arango_ai_sdk.exceptions import AutoRagNotDeployedError, QueryFailedError
   from arango_ai_sdk.models import QueryType

   questions = [
       (QueryType.LOCAL, "Who signed the latest renewal?"),
       (QueryType.GLOBAL, "What themes run through these contracts?"),
       (QueryType.UNIFIED, "Which agreements mention late fees?"),
   ]
   for query_type, question in questions:
       try:
           answer = retriever.ask(question, query_type=query_type)
       except AutoRagNotDeployedError:
           print("Retriever is gone; deploy again.")
           break
       except QueryFailedError as exc:
           print(query_type.name, exc.failure_code, exc.run_id)
       else:
           print(query_type.name, answer.run_id)
           print(answer.result)
