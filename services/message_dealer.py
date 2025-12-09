from json import loads
from pathlib import Path
from typing import Any, Optional


class MessageDealer:
    def __init__(self, file_path: str = "messages.json"):
        path = Path(file_path)
        with path.open("r", encoding="utf-8") as messages_file:
            self.all_messages = loads(messages_file.read())

    def _get(self, section: str, key: str) -> Optional[str]:
        return self.all_messages.get(section, {}).get(key)

    def get_error(self, key: str) -> str:
        return self._get("errors", key) or self.all_messages["errors"]["default"]

    def get_error_message(self, key: str) -> str:
        return self.get_error(key)

    def get_registration_message(self, key: str) -> Optional[str]:
        return self._get("registration", key)

    def get_functional_message(self, key: str) -> Optional[str]:
        return self._get("functional", key)

    def get_ui(self, key: str) -> Optional[str]:
        return self._get("ui", key)

    def get_map_message(self, *, user_name1: str, score1: int, user_name2: str, score2: int, total_score: int, day: int = 1) -> str:
        template = self._get("map_message", "caption") or "{user_name1}: {score1}, {user_name2}: {score2}. Итог: {total_score}"
        data: dict[str, Any] = {
            "user_name1": user_name1,
            "score1": score1,
            "user_name2": user_name2,
            "score2": score2,
            "total_score": total_score,
            "day": day,
        }
        return template.format(**data)




