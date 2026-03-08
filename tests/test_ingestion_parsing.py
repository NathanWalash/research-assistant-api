from research_assistant_api.ingestion.service import parse_dataset_row


def test_parse_dataset_row_assigns_single_institution_and_skips_incomplete_authors() -> None:
    parsed = parse_dataset_row(
        {
            "id": "https://openalex.org/W100",
            "display_name": "Parsing Paper",
            "abstract": "Structured abstract",
            "publication_year": "2024",
            "publication_date": "2024-02-01",
            "cited_by_count": "7",
            "doi": "https://doi.org/10.1234/parse",
            "primary_location.source.display_name": "Parsing Journal",
            "language": "en",
            "type": "article",
            "primary_topic.display_name": "Machine Learning",
            "authorships.institutions.display_name": "University of Leeds",
            "authorships.institutions.id": "https://openalex.org/I1",
            "authorships.countries": "GB|GB",
            "authorships.author.display_name": "Alice Smith|",
            "authorships.author.id": "https://openalex.org/A1|",
            "authorships.author.orcid": "https://orcid.org/0000-0000-0000-0001|",
            "authorships.is_corresponding": "True|False",
        }
    )

    assert parsed.topic == {
        "id": "topic:machine-learning",
        "name": "Machine Learning",
        "field": None,
    }
    assert parsed.institutions == [
        {
            "id": "https://openalex.org/I1",
            "name": "University of Leeds",
            "country": "GB",
        }
    ]
    assert parsed.authors == [
        {
            "id": "https://openalex.org/A1",
            "name": "Alice Smith",
            "orcid": "https://orcid.org/0000-0000-0000-0001",
            "institution_id": "https://openalex.org/I1",
        }
    ]
    assert parsed.authorships == [
        {
            "paper_id": "https://openalex.org/W100",
            "author_id": "https://openalex.org/A1",
            "author_position": 1,
            "is_corresponding": True,
        }
    ]


def test_parse_dataset_row_leaves_author_institution_unset_for_multi_institution_rows() -> None:
    parsed = parse_dataset_row(
        {
            "id": "https://openalex.org/W101",
            "display_name": "Multi Institution Paper",
            "abstract": "",
            "publication_year": "2023",
            "publication_date": "2023-11-10",
            "cited_by_count": "0",
            "doi": "",
            "primary_location.source.display_name": "Journal Two",
            "language": "en",
            "type": "article",
            "primary_topic.display_name": "Data Engineering",
            "authorships.institutions.display_name": "University of Leeds|MIT",
            "authorships.institutions.id": "https://openalex.org/I1|https://openalex.org/I2",
            "authorships.countries": "GB|US",
            "authorships.author.display_name": "Dana Smith",
            "authorships.author.id": "https://openalex.org/A9",
            "authorships.author.orcid": "",
            "authorships.is_corresponding": "False",
        }
    )

    assert parsed.authors == [
        {
            "id": "https://openalex.org/A9",
            "name": "Dana Smith",
            "orcid": None,
            "institution_id": None,
        }
    ]
    assert parsed.institutions == [
        {
            "id": "https://openalex.org/I1",
            "name": "University of Leeds",
            "country": None,
        },
        {
            "id": "https://openalex.org/I2",
            "name": "MIT",
            "country": None,
        },
    ]
