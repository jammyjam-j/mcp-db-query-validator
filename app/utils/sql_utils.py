Let's open that file mentally. Probably it imports from utils.sql_utils. We need to guess usage. Likely parse SQL, check for prohibited statements like DROP, INSERT etc. Maybe validate SELECT only.

Implement functions: is_safe_query(sql:str)->bool; maybe get_tables_from_sql(sql). Use sqlparse library? Check requirements.txt.Open mentally: likely includes fastapi, pydantic, sqlalchemy, uvicorn, pytest, etc. Might include sqlparse. If not, we can add dependency but can't modify. Assume sqlparse present.

Implement:

- tokenize_sql(sql) returns list of tokens using sqlparse.
- is_select_statement(sql)
- contains_prohibited_keywords(sql, prohibited_list)
- extract_table_names(sql)

Also maybe function to check if query references only allowed tables. Use regex? Let's implement robustly with sqlparse.

Return bool safe.

Add custom exception: UnsafeQueryError.

Implement accordingly.import re
from typing import List

import sqlparse
from sqlparse.sql import IdentifierList, Identifier, TokenList
from sqlparse.tokens import DML, Keyword, Name


class UnsafeQueryError(RuntimeError):
    pass


def _extract_identifiers(token: TokenList) -> List[str]:
    identifiers = []
    for token in token:
        if isinstance(token, IdentifierList):
            for identifier in token.get_identifiers():
                if isinstance(identifier, Identifier):
                    identifiers.append(identifier.get_real_name())
        elif isinstance(token, Identifier):
            identifiers.append(token.get_real_name())
    return identifiers


def _find_table_names(parsed: sqlparse.sql.Statement) -> List[str]:
    table_names = []
    from_seen = False
    for token in parsed.tokens:
        if from_seen:
            if isinstance(token, IdentifierList):
                table_names.extend(_extract_identifiers(token))
                break
            elif isinstance(token, Identifier):
                table_names.append(token.get_real_name())
                break
        if token.ttype is Keyword and token.value.upper() == "FROM":
            from_seen = True
    return table_names


def _is_select_statement(parsed: sqlparse.sql.Statement) -> bool:
    for token in parsed.tokens:
        if token.ttype is DML and token.value.upper() == "SELECT":
            return True
    return False


def contains_prohibited_keywords(sql: str, prohibited: List[str]) -> bool:
    lowered = sql.lower()
    for word in prohibited:
        pattern = rf"\b{re.escape(word.lower())}\b"
        if re.search(pattern, lowered):
            return True
    return False


def extract_table_names(sql: str) -> List[str]:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return []
    statement = parsed[0]
    return _find_table_names(statement)


def is_select_statement(sql: str) -> bool:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return False
    statement = parsed[0]
    return _is_select_statement(statement)


def validate_sql_query(
    sql: str,
    allowed_tables: List[str] | None = None,
    prohibited_keywords: List[str] | None = None,
) -> None:
    if not is_select_statement(sql):
        raise UnsafeQueryError("Only SELECT statements are permitted.")
    if prohibited_keywords and contains_prohibited_keywords(sql, prohibited_keywords):
        raise UnsafeQueryError(f"Prohibited keywords detected: {prohibited_keywords}.")
    tables_in_query = extract_table_names(sql)
    if allowed_tables is not None:
        for table in tables_in_query:
            if table.lower() not in [t.lower() for t in allowed_tables]:
                raise UnsafeQueryError(
                    f"Table '{table}' is not in the list of allowed tables."
                )
    return None

def sanitize_sql(sql: str) -> str:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return ""
    statement = parsed[0]
    tokens = []
    for token in statement.tokens:
        if token.ttype is Keyword and token.value.upper() == "SELECT":
            continue
        if token.ttype is DML and token.value.upper() == "FROM":
            continue
        tokens.append(token.value)
    sanitized = " ".join(tokens).strip()
    return sanitized

def get_first_table_name(sql: str) -> str | None:
    tables = extract_table_names(sql)
    return tables[0] if tables else None

def normalize_sql(sql: str) -> str:
    parsed = sqlparse.parse(sql)
    if not parsed:
        return ""
    statement = parsed[0]
    formatted = sqlparse.format(str(statement), reindent=True, keyword_case="upper")
    return formatted.strip()