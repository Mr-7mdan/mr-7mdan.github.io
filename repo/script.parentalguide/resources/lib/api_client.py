import requests
import xbmcaddon

ADDON = xbmcaddon.Addon()

# Server-side aggregator. It scrapes every provider itself, so the addon
# fetches from here instead of scraping provider sites client-side.
DEFAULT_ENDPOINT = "https://pg-2.vercel.app"

# addon/skin provider labels -> server provider names.
# RaisingChildren has no server equivalent; it maps through lowercased and the
# server returns an error, which we surface as None.
PROVIDER_MAP = {
    "IMDB": "imdb",
    "KidsInMind": "kidsinmind",
    "MovieGuide": "movieguide",
    "DoveFoundation": "dove",
    "CSM": "commonsense",
    "ParentPreviews": "parentpreview",
}


def map_provider(label):
    return PROVIDER_MAP.get(label, str(label).lower())


def get_parental_guide(imdb_id=None, video_name=None, release_year=None, provider="imdb"):
    # Calls GET /get_data. Returns the review dict (keys: id, title, provider,
    # recommended-age, review-items[{name,cat,description,votes}], review-link)
    # or None on any error / empty / provider failure.
    endpoint = (ADDON.getSetting("api_endpoint") or DEFAULT_ENDPOINT).rstrip("/")
    params = {"provider": provider}
    if imdb_id:
        params["imdb_id"] = imdb_id
    if video_name:
        params["video_name"] = video_name
    if release_year:
        params["release_year"] = str(release_year)
    try:
        resp = requests.get(
            endpoint + "/get_data",
            params=params,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=45,
        )
        data = resp.json()
    except Exception:
        return None
    if not isinstance(data, dict) or data.get("error"):
        return None
    return data
