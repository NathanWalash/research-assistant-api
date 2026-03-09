# Demo Flow

Use this order for a short coursework walkthrough:

1. Search the Leeds corpus with `GET /papers/search`.
2. Open a paper record with `GET /papers/{id}`.
3. Show semantic retrieval with `GET /papers/{id}/similar`.
4. Show citation-neighbourhood lookup with `GET /papers/{id}/citations`.
5. Register and log in.
6. Create a project.
7. Add papers to the project reading list.
8. Show `GET /projects/{id}/recommendations`.
9. Compare `mode=semantic`, `mode=citation`, and `mode=hybrid`.

Consistent report wording:

- citation counts support influence analytics
- citation traversal is limited to the Leeds citation subgraph generated from OpenAlex
- recommendation scoring is configurable so the trade-off between semantic similarity and citation proximity is explicit
