from dataclasses import dataclass

PAGE_QUERY_ARGUMENT = "page"


@dataclass
class PaginationContext:
    current_page: int
    page_size: int

    def get_offset(self) -> int:
        return (self.current_page - 1) * self.page_size

    def get_limit(self) -> int:
        return self.page_size

    def get_total_pages_count(self, total_result_count: int) -> int:
        return (total_result_count // self.page_size) + min(
            1, total_result_count % self.page_size
        )
