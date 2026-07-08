import logging

from src.clients import arxiv_client, openalex_client


class _DummyResponse:
    def __init__(self, payload=None, text="", status_code=200):
        self._payload = payload or {}
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self):
        return self._payload


class _DummyFeed:
    def __init__(self, entries):
        self.entries = entries


def test_openalex_pagination_collects_multiple_pages(monkeypatch) -> None:
    call_pages = []

    def fake_get(url, params, timeout):
        call_pages.append(params["page"])
        if params["page"] == 1:
            return _DummyResponse(payload={"results": [{"id": "W1"}, {"id": "W2"}]})
        if params["page"] == 2:
            return _DummyResponse(payload={"results": [{"id": "W3"}, {"id": "W4"}]})
        return _DummyResponse(payload={"results": []})

    monkeypatch.setattr(openalex_client.requests, "get", fake_get)

    records, source_log = openalex_client.search_papers(
        query_config={"id": "Q01", "text": "6G", "topic_cluster": "6G"},
        settings={"max_results_per_query": 3, "page_size": 2, "max_pages": 5},
        logger=logging.getLogger("test"),
    )

    assert [record["id"] for record in records] == ["W1", "W2", "W3"]
    assert source_log["returned_record_count"] == 3
    assert call_pages == [1, 2]


def test_arxiv_pagination_collects_multiple_pages(monkeypatch) -> None:
    call_starts = []

    def fake_get(url, params, timeout):
        call_starts.append(params["start"])
        return _DummyResponse(text=f"start:{params['start']}")

    def fake_parse(text):
        if text == "start:0":
            return _DummyFeed(
                entries=[
                    {
                        "id": "a1",
                        "title": "T1",
                        "summary": "S1",
                        "published": "2025-01-01T00:00:00Z",
                        "authors": [],
                        "tags": [],
                        "links": [],
                    },
                    {
                        "id": "a2",
                        "title": "T2",
                        "summary": "S2",
                        "published": "2025-01-02T00:00:00Z",
                        "authors": [],
                        "tags": [],
                        "links": [],
                    },
                ]
            )
        if text == "start:2":
            return _DummyFeed(
                entries=[
                    {
                        "id": "a3",
                        "title": "T3",
                        "summary": "S3",
                        "published": "2025-01-03T00:00:00Z",
                        "authors": [],
                        "tags": [],
                        "links": [],
                    },
                    {
                        "id": "a4",
                        "title": "T4",
                        "summary": "S4",
                        "published": "2025-01-04T00:00:00Z",
                        "authors": [],
                        "tags": [],
                        "links": [],
                    },
                ]
            )
        return _DummyFeed(entries=[])

    monkeypatch.setattr(arxiv_client.requests, "get", fake_get)
    monkeypatch.setattr(arxiv_client.feedparser, "parse", fake_parse)
    monkeypatch.setattr(arxiv_client, "_respect_rate_limit", lambda settings: None)

    records, source_log = arxiv_client.search_papers(
        query_config={"id": "Q01", "text": "6G", "topic_cluster": "6G"},
        settings={"max_results_per_query": 3, "page_size": 2, "max_pages": 5, "retry_on_429": 0},
        logger=logging.getLogger("test"),
    )

    assert [record["id"] for record in records] == ["a1", "a2", "a3"]
    assert source_log["returned_record_count"] == 3
    assert call_starts == [0, 2]
