# API Examples

Note: `GET /analytics/collaborations` is no longer available. It was removed
because the co-authorship aggregation query was too slow for interactive usage.

## Register

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strong-password"
}
```

## Search Papers

```http
GET /papers/search?query=knowledge%20graphs&limit=5
```

## Search Authors

```http
GET /authors/search?query=alice&limit=5
```

## Paper Detail

```http
GET /papers/https://openalex.org/W123
```

## Similar Papers

```http
GET /papers/https://openalex.org/W123/similar?limit=5
```

## Citation Neighbourhood

```http
GET /papers/https://openalex.org/W123/citations
```

## Directed Citation Path

```http
GET /papers/https://openalex.org/W123/path/https://openalex.org/W456?max_depth=6
```

## Create Project

```http
POST /projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Dissertation project",
  "description": "Core reading list"
}
```

## Add Reading-List Item

```http
POST /projects/{project_id}/reading-list
Authorization: Bearer <token>
Content-Type: application/json

{
  "paper_id": "https://openalex.org/W123",
  "priority": "high",
  "notes": "Read first"
}
```

## Project Recommendations

Semantic only:

```http
GET /projects/{project_id}/recommendations?mode=semantic
Authorization: Bearer <token>
```

Citation only:

```http
GET /projects/{project_id}/recommendations?mode=citation
Authorization: Bearer <token>
```

Hybrid with manual weighting:

```http
GET /projects/{project_id}/recommendations?mode=hybrid&semantic_weight=0.8&citation_weight=0.2
Authorization: Bearer <token>
```

## Annotation Workflow

```http
POST /papers/https://openalex.org/W123/annotations
Authorization: Bearer <token>
Content-Type: application/json

{
  "text": "Useful methodology paper"
}
```

```http
GET /papers/https://openalex.org/W123/annotations
Authorization: Bearer <token>
```
