import requests

# IMDb's public GraphQL endpoint. Replaces the old HTML scrape of
# /title/<id>/parentalguide, whose DOM IMDb removed (headerless requests
# now get 403, and a browser UA gets a 202 JS-challenge with no data).
GRAPHQL_URL = "https://caching.graphql.imdb.com/"

_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

_QUERY = """
query PG($id: ID!) {
  title(id: $id) {
    parentsGuide {
      categories {
        category { text }
        severity { text votedFor }
        totalSeverityVotes
        guideItems(first: 50) {
          edges { node { isSpoiler text { plainText } } }
        }
      }
    }
  }
}
"""


def imdb_parentsguide(tid):
    # Returns a list of advisory dicts: {name, score, description, cat, votes}.
    # Same contract the old HTML scraper produced, so scraper.py/viewer are
    # unchanged. Returns [] on any failure instead of raising.
    try:
        resp = requests.post(
            GRAPHQL_URL,
            headers=_HEADERS,
            json={"query": _QUERY, "variables": {"id": tid}},
            timeout=15,
        )
        categories = resp.json()["data"]["title"]["parentsGuide"]["categories"] or []
    except Exception:
        return []

    advisory = []
    for cat in categories:
        severity = (cat.get("severity") or {})
        sev_text = severity.get("text") or ""
        if sev_text in [None, ""]:
            continue

        # Non-spoiler scenes only, matching the old default view.
        edges = (cat.get("guideItems") or {}).get("edges") or []
        scenes = [
            e["node"]["text"]["plainText"]
            for e in edges
            if e.get("node") and not e["node"].get("isSpoiler")
            and e["node"].get("text") and e["node"]["text"].get("plainText")
        ]

        voted_for = severity.get("votedFor")
        total = cat.get("totalSeverityVotes")
        votes = ""
        if voted_for is not None and total is not None:
            votes = "%s of %s found this %s" % (voted_for, total, sev_text)

        advisory.append({
            "name": cat["category"]["text"],
            "score": "",
            "description": "\n".join(scenes),
            "cat": sev_text,  # None/Mild/Moderate/Severe -> tags/<cat>.png
            "votes": votes,
        })
    return advisory


if __name__ == "__main__":
    # Manual check (needs network): python3 resources/lib/imdb.py
    data = imdb_parentsguide("tt0111161")
    assert data, "expected non-empty advisory list"
    assert all(d["cat"] in ("None", "Mild", "Moderate", "Severe") for d in data), \
        "severity must match tag icon filenames"
    assert any(d["description"] for d in data), "expected at least one scene description"
    print("OK: %d categories" % len(data))
    for d in data:
        print(" -", d["name"], "|", d["cat"], "|", d["votes"])
