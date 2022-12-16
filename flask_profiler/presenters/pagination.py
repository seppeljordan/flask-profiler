from copy import copy
from dataclasses import dataclass
from typing import Iterator
from urllib.parse import ParseResult, parse_qs, urlencode

from flask_profiler.pagination import PAGE_QUERY_ARGUMENT


@dataclass
class Page:
    label: str
    link_target: str


class Paginator:
    def __init__(self, target_link: ParseResult, total_page_count: int) -> None:
        self.target_link = target_link
        self.total_page_count = total_page_count

    def __iter__(self) -> Iterator[Page]:
        for n in range(1, self.total_page_count + 1):
            yield Page(
                label=str(n),
                link_target=self.get_page_link(n),
            )

    def get_page_link(self, n: int) -> str:
        query = dict(parse_qs(self.target_link.query))
        query[PAGE_QUERY_ARGUMENT] = [str(n)]
        link = copy(self.target_link)
        link = link._replace(
            query=urlencode({key: value[0] for key, value in query.items()})
        )
        return link.geturl()
