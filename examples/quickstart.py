"""AutoGraph end to end: load -> build -> retrieve.

Environment: ARANGO_URL, ARANGO_USERNAME, ARANGO_PASSWORD, ARANGO_DATABASE,
plus OPENAI_API_KEY for the LLM credential.
"""

import os

from arango_ai import Client

client = Client.from_env()

# Registers an AutoGraph-typed project, stores the key as a secret profile,
# deploys the AutoGraph service, and waits until it actually serves.
project = client.autograph.create_project(
    "quickstart", openai_api_key=os.environ["OPENAI_API_KEY"]
)

# Load: upload documents (a folder, paths, or a glob) into a category.
project.add_files("./docs", category="knowledge")

# Build: corpus graph -> strategy plan -> knowledge graph.
project.build().wait()
plan = project.strategize("moderate")  # blocking; returns the plan for review
print(f"strategies: {plan['totalStrategies']}")
project.orchestrate().wait()

# Retrieve: deploy a retriever (reuses the project's model settings) and ask.
project.deploy_retriever()
print(project.ask("What are the main topics in these documents?"))

# Streaming variant:
# for event in project.ask_stream("...", mode="DEEP_SEARCH"):
#     ...

# Cleanup when done evaluating:
# project.delete()
