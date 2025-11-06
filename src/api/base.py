from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import time
import requests
from ..utils.logger import logger

@dataclass
class Market:
    platform: str
    market_id: str
    question: str
    yes_price: float
    no_price: float
    liquidity: Optional[float]
    volume: Optional[float]
    end_date: Optional[datetime]
    raw_data: Dict[str, Any]

    def __repr__(self):
        return (f"Market(platform={self.platform}, question='{self.question}', "
                f"yes={self.yes_price:.3f}, no={self.no_price:.3f})")

class BaseAPIClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.cache = {}
        self.cache_ttl = 10

    def _get_cached(self, key: str) -> Optional[Any]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return data
            else:
                del self.cache[key]
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        self.cache[key] = (data, time.time())

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise

    def get_markets(self):
        raise NotImplementedError("Subclasses must implement get_markets()")
