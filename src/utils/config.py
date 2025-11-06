import os
import yaml
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self._resolve_env_vars(self.config)

    def _resolve_env_vars(self, d: Dict[str, Any]) -> None:
        for key, value in d.items():
            if isinstance(value, dict):
                self._resolve_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                d[key] = os.getenv(env_var, "")

    def get(self, *keys):
        result = self.config
        for key in keys:
            result = result[key]
        return result

config = Config()
