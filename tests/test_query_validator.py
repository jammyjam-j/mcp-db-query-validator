Let's inspect query_validator code.import pytest
from app.services.query_validator import QueryValidator

@pytest.fixture(scope="module")
def validator() -> QueryValidator:
    return QueryValidator()

def test_valid_select_statement(validator):
    sql = "SELECT id, name FROM users WHERE active = 1"
    assert validator.validate(sql) is True

def test_valid_insert_statement(validator):
    sql = "INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com')"
    assert validator.validate(sql) is True

def test_invalid_drop_table_statement(validator):
    sql = "DROP TABLE users"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_invalid_update_statement(validator):
    sql = "UPDATE users SET active = 0 WHERE id = 5"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_empty_sql_string(validator):
    sql = ""
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_none_input_raises_type_error():
    validator = QueryValidator()
    with pytest.raises(TypeError):
        validator.validate(None)

def test_multiple_statements_with_semicolon_disallowed(validator):
    sql = "SELECT * FROM users; DROP TABLE users;"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_comments_is_valid(validator):
    sql = "-- This is a comment\nSELECT id FROM users"
    assert validator.validate(sql) is True

def test_select_statement_with_subquery(validator):
    sql = "SELECT u.id, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count FROM users u"
    assert validator.validate(sql) is True

def test_insert_with_multiline_values(validator):
    sql = """
    INSERT INTO users (name, email)
    VALUES
        ('Bob', 'bob@example.com'),
        ('Carol', 'carol@example.net')
    """
    assert validator.validate(sql) is True

def test_statement_with_unallowed_keyword_case_insensitive(validator):
    sql = "SeLeCt * From Users"
    assert validator.validate(sql) is True

def test_sql_with_non_ascii_characters_valid(validator):
    sql = "SELECT * FROM users WHERE name LIKE 'José%'"
    assert validator.validate(sql) is True

def test_select_statement_without_from_clause_raises_error(validator):
    sql = "SELECT 1 + 1"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_insert_into_nonexistent_table_raises_error(validator):
    sql = "INSERT INTO nonexistent (col) VALUES ('val')"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_update_statement_with_where_clause_allowed_if_disabled_in_config():
    validator = QueryValidator()
    validator.allow_updates = False
    sql = "UPDATE users SET active = 0 WHERE id = 10"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_allowing_updates_permits_update_statements(validator):
    validator.allow_updates = True
    sql = "UPDATE users SET active = 1 WHERE id = 3"
    assert validator.validate(sql) is True

def test_sql_with_trailing_semicolon_valid_if_allowed():
    validator = QueryValidator()
    validator.allow_trailing_semicolon = True
    sql = "SELECT * FROM users;"
    assert validator.validate(sql) is True

def test_sql_without_trailing_semicolon_invalid_if_required():
    validator = QueryValidator()
    validator.require_trailing_semicolon = True
    sql = "SELECT * FROM users"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_validator_with_custom_allowed_tables(validator):
    validator.allowed_tables = {"users", "orders"}
    sql = "INSERT INTO orders (user_id, amount) VALUES (1, 100)"
    assert validator.validate(sql) is True
    sql_invalid = "INSERT INTO payments (amount) VALUES (50)"
    with pytest.raises(ValueError):
        validator.validate(sql_invalid)

def test_validator_skips_comments_and_whitespace_only(validator):
    sql = "\n\n-- Only comment\n   \t  "
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_nested_subquery_in_where_clause_valid(validator):
    sql = """
    SELECT * FROM users
    WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)
    """
    assert validator.validate(sql) is True

def test_validator_handles_long_query_without_error(validator):
    long_values = ", ".join([f"('{i}', 'email{i}@example.com')" for i in range(1000)])
    sql = f"INSERT INTO users (name, email) VALUES {long_values}"
    assert validator.validate(sql) is True

def test_validator_raises_value_error_on_sql_with_unmatched_parentheses(validator):
    sql = "SELECT * FROM users WHERE (id = 5"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_validator_accepts_properly_escaped_strings_in_query(validator):
    sql = "SELECT * FROM users WHERE name = 'O''Reilly'"
    assert validator.validate(sql) is True

def test_sql_with_backticks_and_aliases_valid(validator):
    sql = "SELECT u.id AS user_id, o.total FROM `users` u JOIN orders o ON u.id = o.user_id"
    assert validator.validate(sql) is True

def test_validator_rejects_dangerous_drop_view_statement(validator):
    sql = "DROP VIEW user_view"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_schema_qualified_table_name_valid(validator):
    sql = "SELECT * FROM public.users"
    assert validator.validate(sql) is True

def test_validator_rejects_unqualified_table_not_in_allowed_list(validator):
    validator.allowed_tables = {"public.users"}
    sql = "SELECT * FROM users"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_cross_join_valid(validator):
    sql = "SELECT a.id, b.id FROM users a CROSS JOIN orders b"
    assert validator.validate(sql) is True

def test_validator_handles_empty_values_clause_in_insert(validator):
    sql = "INSERT INTO users (name, email) VALUES ()"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_complex_aggregates_and_group_by_valid(validator):
    sql = """
    SELECT department, COUNT(*) as cnt
    FROM employees
    GROUP BY department
    HAVING cnt > 5
    """
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_experimental_feature_keyword(validator):
    sql = "SELECT * FROM users WITH (NOLOCK)"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_date_literal_valid(validator):
    sql = "SELECT * FROM events WHERE event_date >= '2023-01-01'"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_unescaped_backslashes_in_string(validator):
    sql = r"SELECT * FROM logs WHERE message LIKE 'Error\\%';"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_dollar_quoted_strings_valid(validator):
    sql = """SELECT $tag$This is a tag$tag$ FROM dual"""
    assert validator.validate(sql) is True

def test_validator_accepts_query_with_window_function(validator):
    sql = """
    SELECT id, ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
    FROM users
    WHERE active = 1
    """
    assert validator.validate(sql) is True

def test_sql_with_cte_valid(validator):
    sql = """
    WITH recent AS (
        SELECT * FROM orders WHERE order_date > '2023-01-01'
    )
    SELECT r.id, r.total FROM recent r
    """
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_system_table_access(validator):
    sql = "SELECT * FROM pg_catalog.pg_tables"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_json_field_extraction_valid(validator):
    sql = "SELECT data->>'name' as name FROM users WHERE id = 1"
    assert validator.validate(sql) is True

def test_validator_handles_query_with_line_continuation_backslash(validator):
    sql = "SELECT * \\\nFROM users"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_multiple_allowed_tables_valid(validator):
    validator.allowed_tables = {"users", "orders", "products"}
    sql = "INSERT INTO products (name, price) VALUES ('Widget', 9.99)"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_using_unallowed_function(validator):
    sql = "SELECT pg_sleep(5);"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_alias_underscore_valid(validator):
    sql = "SELECT u.* FROM users AS u"
    assert validator.validate(sql) is True

def test_validator_handles_query_with_unclosed_string_literal(validator):
    sql = "SELECT * FROM users WHERE name = 'Bob"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_escaped_quotes_in_identifier_valid(validator):
    sql = 'SELECT "user""s" FROM "public"."users"'
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_broken_syntax(validator):
    sql = "SELEC * FROM users"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_view_access_valid_if_allowed(validator):
    validator.allowed_tables = {"public.user_view"}
    sql = "SELECT * FROM public.user_view"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_prohibited_keyword_in_comment(validator):
    sql = "-- DROP TABLE users\nSELECT 1"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_limit_clause_valid(validator):
    sql = "SELECT * FROM users LIMIT 10 OFFSET 5"
    assert validator.validate(sql) is True

def test_validator_handles_query_with_case_statement(validator):
    sql = """
    SELECT id,
           CASE WHEN active THEN 'Yes' ELSE 'No' END as active_flag
    FROM users
    """
    assert validator.validate(sql) is True

def test_sql_with_schema_qualified_view_valid(validator):
    sql = "SELECT * FROM public.user_view"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_trailing_comment_after_query(validator):
    sql = "SELECT * FROM users -- fetch all"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_union_all_valid(validator):
    sql = """
    SELECT id, name FROM customers
    UNION ALL
    SELECT id, name FROM suppliers
    """
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_nonexistent_table_and_allow_any_table_disabled(validator):
    validator.allowed_tables = {"users"}
    sql = "SELECT * FROM orders"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_different_quote_styles_valid(validator):
    sql = 'SELECT \'single\' AS s, "double" AS d'
    assert validator.validate(sql) is True

def test_validator_handles_empty_query_after_strip(validator):
    sql = "   \n  "
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_backtick_aliases_valid(validator):
    sql = "SELECT `u`.id FROM `users` AS `u`"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_unsafe_cast(validator):
    sql = "SELECT CAST('1' AS BIGINT);"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_group_by_having_valid(validator):
    sql = """
    SELECT category, COUNT(*) FROM products
    GROUP BY category HAVING COUNT(*) > 10
    """
    assert validator.validate(sql) is True

def test_validator_handles_select_with_subselect_in_from_clause(validator):
    sql = "SELECT * FROM (SELECT id FROM users WHERE active=1) AS sub"
    assert validator.validate(sql) is True

def test_sql_with_unnest_function_valid(validator):
    sql = "SELECT unnest(array[1,2,3]) AS num"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_syntax_error_at_end(validator):
    sql = "SELECT * FROM users WHERE id = 5 AND"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_window_partition_by_valid(validator):
    sql = """
    SELECT department, AVG(salary) OVER (PARTITION BY department) AS avg_salary
    FROM employees
    """
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_illegal_escaped_char_in_string(validator):
    sql = "SELECT 'Line1\\nLine2' FROM dual"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_boolean_literal_valid(validator):
    sql = "SELECT * FROM users WHERE active = TRUE"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_using_nonexistent_function(validator):
    sql = "SELECT nonexistent_func(1);"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_case_insensitive_keywords_valid(validator):
    sql = "select * from users where active = true"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_malformed_json_extract(validator):
    sql = "SELECT json_data->'missing_key' FROM events"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_cross_apply_valid(validator):
    sql = """
    SELECT a.id, b.value
    FROM users AS a CROSS APPLY (
        SELECT TOP 1 value FROM user_details WHERE user_id = a.id ORDER BY created_at DESC
    ) AS b
    """
    assert validator.validate(sql) is True

def test_validator_handles_query_with_trailing_whitespace_and_semicolon(validator):
    sql = "SELECT * FROM users ;   "
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_date_time_literal_valid(validator):
    sql = "SELECT * FROM events WHERE event_timestamp >= '2023-01-01 10:00:00'"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_unescaped_backticks_in_identifier(validator):
    sql = "SELECT `user`name` FROM users"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_unnest_of_jsonb_array_valid(validator):
    sql = "SELECT jsonb_array_elements_text(data) AS item FROM logs"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_illegal_keyword_in_comment_after_semicolon(validator):
    sql = "SELECT 1; -- DROP TABLE users"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_with_coalesce_function_valid(validator):
    sql = "SELECT COALESCE(name, 'Unknown') FROM users"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_unsafe_substring_length_specified(validator):
    sql = "SELECT SUBSTRING('abcdef', 1, -5);"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_array_literal_valid(validator):
    sql = "SELECT ARRAY[1,2,3] AS nums"
    assert validator.validate(sql) is True

def test_validator_handles_query_with_complex_boolean_expression_valid(validator):
    sql = """
    SELECT * FROM users
    WHERE (active = TRUE AND last_login > '2023-01-01')
      OR (role = 'admin' AND login_attempts < 5)
    """
    assert validator.validate(sql) is True

def test_sql_with_schema_qualified_function_call_valid(validator):
    sql = "SELECT public.my_func('arg') FROM dual"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_malicious_regex_pattern(validator):
    sql = "SELECT REGEXP_SUBSTR('test', '.*');"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_qualifier_in_insert_valid(validator):
    sql = "INSERT INTO public.users (name) VALUES ('Dave')"
    assert validator.validate(sql) is True

def test_validator_rejects_statement_with_illegal_escape_sequence_in_string(validator):
    sql = r"SELECT 'This is a backslash: \\';"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_current_timestamp_valid(validator):
    sql = "SELECT CURRENT_TIMESTAMP FROM dual"
    assert validator.validate(sql) is True

def test_validator_handles_query_with_window_frame_specification_valid(validator):
    sql = """
    SELECT id,
           SUM(amount) OVER (PARTITION BY category
                             ORDER BY created_at
                             RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
    FROM orders
    """
    assert validator.validate(sql) is True

def test_sql_with_unqualified_table_and_no_allowed_tables_set(validator):
    validator.allowed_tables = set()
    sql = "SELECT * FROM users"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_validator_rejects_statement_with_illegal_use_of_cast_in_select(validator):
    sql = "SELECT CAST('abc' AS INTEGER) FROM dual"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_sql_using_json_build_object_valid(validator):
    sql = "SELECT jsonb_build_object('id', id, 'name', name) FROM users"
    assert validator.validate(sql) is True

def test_validator_handles_query_with_complex_nested_subqueries_valid(validator):
    sql = """
    SELECT u.id, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count
    FROM users u
    WHERE EXISTS (
        SELECT 1 FROM user_roles r WHERE r.user_id = u.id AND r.role = 'admin'
    )
    """
    assert validator.validate(sql) is True

def test_sql_with_invalid_function_name_syntax(validator):
    sql = "SELECT * FROM users WHERE fncname()"
    with pytest.raises(ValueError):
        validator.validate(sql)

def test_validator_rejects_statement_with_unescaped_single_quote_in_string_literal(validator):
    sql = "SELECT 'O'Reilly' FROM dual"
    with pytest.raises(ValueError):
        validator.validate(sql)