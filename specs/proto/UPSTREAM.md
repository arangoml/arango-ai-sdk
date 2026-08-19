# Vendored proto contracts

These files are vendored, unmodified copies. The owning service repo is the
source of truth; this copy exists so codegen is reproducible and reviewable
without a checkout of the service.

| File | Upstream repo | Pinned commit |
|------|---------------|---------------|
| `corpus_graph.proto` | `arangoml/autograph` (`proto/corpus_graph.proto`) | `6671881360401938fe8838612be74e8999b6499e` (2026-08-18) |
| `google/api/annotations.proto`, `google/api/http.proto` | same (vendored there from googleapis) | same |

## Sync procedure

1. Copy the new `proto/corpus_graph.proto` (and `google/api/*` if changed)
   from the autograph repo.
2. Update the pinned commit in the table above.
3. `make generate` (regenerates `specs/autograph.openapi.yaml` and
   `src/arango_ai/_generated/autograph/`).
4. Commit proto + spec + generated client together in one PR so reviewers see
   the contract change and its client impact side by side.
