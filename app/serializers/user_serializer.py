from typing import Any, Dict

import jsonschema
from pydantic import ValidationError

from app.models.user import User
from app.schemas.user import UserCreateSchema, UserResponseSchema


class UserSerializer:
    def __init__(self) -> None:
        self._create_schema = UserCreateSchema
        self._response_schema = UserResponseSchema

    def serialize(self, user: User) -> Dict[str, Any]:
        try:
            response = self._response_schema.from_orm(user).dict()
        except ValidationError as exc:
            raise ValueError(f"Serialization failed: {exc}") from exc
        return response

    def deserialize_create(self, payload: Dict[str, Any]) -> UserCreateSchema:
        try:
            schema_instance = self._create_schema(**payload)
        except ValidationError as exc:
            raise ValueError(f"Invalid input data: {exc}") from exc
        return schema_instance

    def validate_response(self, data: Dict[str, Any]) -> None:
        try:
            jsonschema.validate(instance=data, schema=self._response_schema.schema())
        except jsonschema.ValidationError as exc:
            raise ValueError(f"Response validation error: {exc.message}") from exc

    def to_json(self, user: User) -> str:
        return json.dumps(self.serialize(user))

    def from_json(self, data: str) -> UserCreateSchema:
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
        return self.deserialize_create(payload)