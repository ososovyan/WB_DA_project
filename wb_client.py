from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional, Union, Generator

from src.base_api_client import _APIInputMixin, _BaseAPIClient, APISettings

@dataclass(frozen=True)
class WBSettings:
    countries: List[str]
    indicators: List[str]
    date_intervals: List[str]
    api: APISettings = field(default_factory=lambda: APISettings(base_url="https://api.worldbank.org/v2", batch_size=1000))

class _WBInputMixin(_APIInputMixin):
    def _extract_data(self, payload: Any) -> List[Dict[str, Any]]:
        if (isinstance(payload, list)
            and len(payload) >= 2
            and isinstance(payload[1], list)
        ):
            return payload[1]
        return []

    def _extract_metadata(self, payload: Any) -> Any:
        if (isinstance(payload, list)
            and len(payload) >= 2
            and isinstance(payload[0], list)
        ):
            return payload[0]
        return {}

    def _get_next_page_params(self, metadata: Any, current_params: Dict[str, Any], page_count: int) -> Optional[Dict[str, Any]]:
        if not metadata or not isinstance(metadata, dict):
            return None

        current_page = metadata.get("page", 1)
        new_params = current_params.copy()
        new_params["page"] = current_page + 1
        return new_params

    def _should_continue_pagination(self, metadata: Any, page_count: int) -> bool:
        if not isinstance(metadata, dict) or not metadata:
            return False

        current_page = metadata.get("page", 1)
        total_pages = metadata.get("pages", 1)
        return current_page < total_pages

    @abstractmethod
    def fetch_all(self, **kwargs) -> Generator[Dict[str, Any], None, None]:
        pass


class WBClient(_WBInputMixin, _BaseAPIClient):
    def __init__(self, wb_set: WBSettings, **kwargs):
        super().__init__(api_set=wb_set.api, **kwargs)
        self.countries: list[str] = wb_set.countries
        self.indicators: list[str] = wb_set.indicators
        self.date_list: list[str] = wb_set.date_intervals

        self.merged_countries: str = ";".join(self.countries) if self.countries else ""
        self.merged_dates = ";".join(map(str, self.date_list)) if self.date_list else ""

    @property
    def params(self) -> Dict[str, Any]:
        params = {
            "format": "json",
            "per_page": self.api_set.batch_size,
            "page": 1,
        }
        # Добавляем дату только если она есть
        if self.merged_dates:
            params["date"] = self.merged_dates
        return params

    def get_endpoints(self) -> Generator[str, None, None]:
        if self.merged_countries:
            for indicator in self.indicators:
                yield f"country/{self.merged_countries}/indicator/{indicator}"
        else:
            for indicator in self.indicators:
                yield f"indicator/{indicator}"

    def fetch_all(self, **kwargs) -> Generator[Dict[str, Any], None, None]:
        for endpoint in self.get_endpoints():
            for _ in self.fetch(endpoint, **kwargs):
                yield _