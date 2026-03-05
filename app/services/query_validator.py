import re
from typing import List

import sqlparse
from sqlparse.sql import IdentifierList, Token
from sqlparse.tokens import DML, Keyword

from app.config import settings


class QueryValidationError(Exception):
    def __init__(self, message: str, query: str) -> None:
        super().__init__(message)
        self.query = query


class QueryValidator:
    _dangerous_keywords: List[str] = [
        "DROP",
        "ALTER",
        "TRUNCATE",
        "REPLACE",
        "MERGE",
        "CALL",
        "EXECUTE",
        "GRANT",
        "REVOKE",
    ]

    def __init__(self, allowed_dml: List[str] | None = None) -> None:
        if allowed_dml is None:
            allowed_dml = settings.ALLOWED_DML_STATEMENTS
        self.allowed_dml = [stmt.upper() for stmt in allowed_dml]

    @staticmethod
    def _extract_tokens(statement) -> List[Token]:
        tokens: List[Token] = []
        for token in statement.tokens:
            if token.is_whitespace or token.ttype is None and not token.value.strip():
                continue
            if isinstance(token, IdentifierList):
                tokens.extend(QueryValidator._extract_tokens(token))
            else:
                tokens.append(token)
        return tokens

    def _is_dangerous(self, token: Token) -> bool:
        if token.ttype in Keyword or token.ttype is None:
            value = token.value.upper()
            for keyword in self._dangerous_keywords:
                if re.match(rf"^{keyword}\b", value):
                    return True
        return False

    def _is_allowed_dml(self, token: Token) -> bool:
        if token.ttype == DML:
            return token.value.upper() in self.allowed_dml
        return True

    def validate(self, query: str) -> None:
        parsed = sqlparse.parse(query)
        if not parsed:
            raise QueryValidationError("Empty or invalid SQL statement", query)

        for stmt in parsed:
            tokens = self._extract_tokens(stmt)
            for token in tokens:
                if self._is_dangerous(token):
                    raise QueryValidationError(
                        f"Dangerous keyword detected: {token.value}", query
                    )
                if not self._is_allowed_dml(token):
                    raise QueryValidationError(
                        f"Disallowed DML statement: {token.value}", query
                    )

        return None

    def is_valid(self, query: str) -> bool:
        try:
            self.validate(query)
            return True
        except QueryValidationError:
            return False

    def validate_and_raise(self, query: str) -> None:
        self.validate(query)