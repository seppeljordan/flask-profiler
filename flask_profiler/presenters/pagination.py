from dataclasses import dataclass
from typing import Iterable, Iterator, Optional, Union
from urllib.parse import ParseResult, parse_qs, urlencode

from flask_profiler.pagination import PAGE_QUERY_ARGUMENT


@dataclass
class Page:
    label: str
    link_target: str
    css_class: str

    @classmethod
    def is_page(self) -> bool:
        return True


class Gap:
    @classmethod
    def is_page(self) -> bool:
        return False


class Paginator:
    def __init__(
        self, target_link: ParseResult, current_page: int, total_page_count: int
    ) -> None:
        self.target_link = target_link
        self.total_page_count = total_page_count
        self.current_page = current_page

    def get_simple_pagination(self) -> Iterator[Page]:
        for n in range(1, self.total_page_count + 1):
            link_target = self._get_page_link(n)
            yield Page(
                label=str(n),
                link_target=link_target,
                css_class=self._get_css_class(page=n),
            )

    def get_truncated_pagination(self) -> Iterator[Union[Page, Gap]]:
        for n in self.get_pages_for_truncated_pagination():
            if n is None:
                yield Gap()
            else:
                link_target = self._get_page_link(n)
                yield Page(
                    label=str(n),
                    link_target=link_target,
                    css_class=self._get_css_class(page=n),
                )

    def get_pages_for_truncated_pagination(self) -> Iterable[Optional[int]]:
        n = 1
        while n <= self.total_page_count:
            if n == 1:
                yield n
                n += 1
            elif abs(self.current_page - n) <= 1:
                yield n
                n += 1
            elif n == self.total_page_count:
                yield n
                n += 1
            else:
                yield None
                if n < self.current_page:
                    n = self.current_page - 1
                elif n < self.total_page_count:
                    n = self.total_page_count

    def _get_page_link(self, n: int) -> str:
        query = dict(parse_qs(self.target_link.query))
        query[PAGE_QUERY_ARGUMENT] = [str(n)]
        link = self.target_link._replace(
            query=urlencode({key: value[0] for key, value in query.items()})
        )
        return link.geturl()

    def _get_css_class(self, page: int) -> str:
        classes = ["pagination-link"]
        if self.current_page == page:
            classes.append("is-current")
        return " ".join(classes)
