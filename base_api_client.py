from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Generator, Union

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.base_client import ClientSettings, _BaseInputMixin, _BaseClient, _BaseOutputMixin


@dataclass(frozen=True)
class APISettings:
    client_set: ClientSettings = field(default_factory=ClientSettings)
    base_url: str = ""
    endpoint: str = ""
    batch_size: int = 1000
    headers: Optional[Dict[str, str]] = field(default=None)
    auth_token: Optional[str] = None

class _BaseAPIClient(_BaseClient):
    def __init__(self, api_set: APISettings, **kwargs):
        super().__init__(api_set.client_set, **kwargs)
        self.api_set = api_set
        self.session: Optional[requests.Session] = None

    def connect(self) -> None:
        if self.session is None:
            self.session = requests.Session()
            if self.api_set.headers:
                self.session.headers.update(self.api_set.headers)
            if self.api_set.auth_token:
                self.session.headers["Authorization"] = f"Bearer {self.api_set.auth_token}"
            self._connected = True

    def disconnect(self) -> None:
        if self.session:
            self.session.close()
            self._connected = False
            self.session = None

    @property
    @abstractmethod
    def params(self) -> Dict[str, Any]:
        """
        Базовый набор параметров запроса
        """
        pass

class APIClientError(Exception):
    pass

class _APIInputMixin( _BaseInputMixin):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIClientError),
        reraise=True,
    )
    def get(
        self: "_BaseAPIClient",
        endpoint: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        if endpoint is None:
            endpoint = self.api_set.endpoint
        if params is None:
            params = self.params
        if not self.session:
            raise APIClientError("Client is not connected")

        url = f"{self.api_set.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.get(url, params=params, timeout=self.api_set.client_set.timeout)
        except requests.RequestException as e:
            raise APIClientError(f"Network error: {e}") from e

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise APIClientError(f"HTTP {response.status_code}: {response.text}") from e

        try:
            payload = response.json()
        except ValueError as exc:
            raise APIClientError("Invalid JSON response") from exc

        return payload

    @abstractmethod
    def _extract_data(self, payload: Any) -> list:
        pass

    @abstractmethod
    def _extract_metadata(self, payload: Any) -> Any:
        pass

    @abstractmethod
    def _should_continue_pagination(self, metadata: Any, page_count: int) -> bool:
        pass

    @abstractmethod
    def _get_next_page_params(self: "_BaseAPIClient", metadata: Any, current_params: Dict, page_count: int) -> Dict:
        pass

    def fetch(
        self: Union["_BaseAPIClient", "_APIInputMixin"],
        endpoint: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        if endpoint is None:
            endpoint = self.api_set.endpoint
        if params is None:
            current_params = self.params.copy()
        else:
            current_params = params.copy()

        page_count = 0

        while True:
            payload = self.get(endpoint, current_params)
            data = self._extract_data(payload)
            metadata = self._extract_metadata(payload)

            if data:
                yield from data

            page_count += 1

            # Проверяем, нужно ли продолжать
            if not self._should_continue_pagination(metadata, page_count):
                break

            # Получаем параметры следующей страницы
            next_params = self._get_next_page_params(metadata, current_params, page_count)
            if not next_params:
                break
            current_params = next_params

class _APIOutputMixin( _BaseOutputMixin):
    """
    Здесь например можно написать логику post методов работы с api
    """
    pass