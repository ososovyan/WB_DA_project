from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from src.logger import AbstractLogger, DefaultLogger


class _BaseMixin(ABC):
    """
    Наследники методы которые могут быть участниками пайплайна
    """
    pass

class _BaseInputMixin(_BaseMixin):
    """
    Наследники-методы могут быть началом пайплайна (source_node)
    """
    pass

class _BaseOutputMixin(_BaseMixin):
    """
    Наследники-методы могут быть окончанием пайплайна (target_node)
    """
    pass

class _BaseInternalMixin(_BaseMixin):
    """
    Наследники-методы могут использоваться до или после пайплайна для изменения внутреннего состояния клиента
    """
    pass


class _BaseIntermediateMixin(_BaseMixin):
    """
    Наследники-методы могут использоваться в качестве промежуточных нод пайплайна (intermediate_node)
    """
    def pass_through(self, data:Any) -> Any:
        return data


@dataclass(frozen=True)
class ClientSettings:
    max_retries: int = 3
    timeout: int = 5
    name: str = "unnamed_client"


class _BaseClient(ABC):
    """
    База для создания класса клиента
    """
    def __init__(
        self,
        settings: ClientSettings,
        logger: Optional[AbstractLogger] = None,
    ):
        self.settings = settings
        self.logger = logger or DefaultLogger(self.__class__.__name__)
        self._connected = False

    @abstractmethod
    def connect(self, **kwargs) -> None:
        """
        Подключение к клиенту
        """
        pass

    @abstractmethod
    def disconnect(self, **kwargs) -> None:
        """
        Отключение от клиента
        """
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _log_operation(self, operation: str, **kwargs):
        self.logger.log("info", f"{self.__class__.__name__}: {operation}", **kwargs)






