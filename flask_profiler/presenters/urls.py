from typing import Dict
from urllib.parse import ParseResult, urlencode, urlparse

from flask import url_for


def get_url_with_query(route: str, url_query: Dict[str, str]) -> ParseResult:
    result = urlparse(url_for(route))._replace(query=urlencode(url_query))
    return result
