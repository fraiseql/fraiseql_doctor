"""File parsing and handling utilities for CLI."""

import json
from pathlib import Path
from typing import Any

import yaml

try:
    from graphql import GraphQLError, build_client_schema, get_introspection_query, parse, validate
except ImportError:
    # Provide a basic fallback if graphql-core is not available
    class GraphQLError(Exception):
        pass

    def parse(query_string):
        # Basic validation - just check it's not empty
        if not query_string.strip():
            raise GraphQLError("Empty query")
        return True


class GraphQLFileHandler:
    """Handle GraphQL file operations."""

    VALID_EXTENSIONS = {".graphql", ".gql", ".query"}

    @staticmethod
    def parse_graphql_file(file_path: Path) -> str:
        """Parse GraphQL file and return query text.

        Args:
        ----
            file_path: Path to GraphQL file

        Returns:
        -------
            GraphQL query text

        Raises:
        ------
            ValueError: If file extension is invalid or parsing fails
            FileNotFoundError: If file doesn't exist

        """
        if file_path.suffix.lower() not in GraphQLFileHandler.VALID_EXTENSIONS:
            raise ValueError(
                f"Invalid file extension '{file_path.suffix}'. "
                f"Expected one of: {', '.join(GraphQLFileHandler.VALID_EXTENSIONS)}"
            )

        try:
            content = file_path.read_text(encoding="utf-8").strip()
            if not content:
                raise ValueError("GraphQL file is empty")

            return content

        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot decode file {file_path}: {e}") from e
        except PermissionError as e:
            raise ValueError(f"Cannot read file {file_path}: {e}") from e

    @staticmethod
    def validate_query_syntax(query: str) -> bool:
        """Validate GraphQL query syntax.

        Args:
        ----
            query: GraphQL query string

        Returns:
        -------
            True if valid, False otherwise

        Raises:
        ------
            ValueError: If query has syntax errors

        """
        try:
            # Parse the query to check syntax
            parsed = parse(query)

            # Basic validation without schema
            # For full validation, we'd need the target GraphQL schema
            if not parsed:
                raise ValueError("Query parsing returned empty result")

            return True

        except GraphQLError as e:
            raise ValueError(f"GraphQL syntax error: {e}") from e
        except Exception as e:
            raise ValueError(f"Query validation failed: {e}") from e

    @staticmethod
    def extract_query_info(query: str) -> dict[str, Any]:
        """Extract information from GraphQL query.

        Args:
        ----
            query: GraphQL query string

        Returns:
        -------
            Dictionary with query information

        """
        try:
            parsed = parse(query)

            operations = []
            fragments = []

            for definition in parsed.definitions:
                if hasattr(definition, "operation"):
                    operations.append(
                        {
                            "operation": definition.operation.value,
                            "name": definition.name.value if definition.name else None,
                            "selection_count": len(definition.selection_set.selections)
                            if definition.selection_set
                            else 0,
                        }
                    )
                elif hasattr(definition, "name") and definition.kind == "fragment_definition":
                    fragments.append(
                        {
                            "name": definition.name.value,
                            "type": definition.type_condition.name.value,
                        }
                    )

            return {
                "operations": operations,
                "fragments": fragments,
                "operation_count": len(operations),
                "fragment_count": len(fragments),
            }

        except Exception as e:
            return {"error": str(e)}


class VariableFileHandler:
    """Handle GraphQL variables file operations."""

    @staticmethod
    def load_variables(file_path: Path) -> dict[str, Any]:
        """Load variables from JSON or YAML file.

        Args:
        ----
            file_path: Path to variables file

        Returns:
        -------
            Dictionary of variables

        Raises:
        ------
            ValueError: If file cannot be parsed
            FileNotFoundError: If file doesn't exist

        """
        try:
            content = file_path.read_text(encoding="utf-8")

            if file_path.suffix.lower() in {".json"}:
                return json.loads(content)
            if file_path.suffix.lower() in {".yaml", ".yml"}:
                return yaml.safe_load(content) or {}
            # Try to auto-detect format
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                try:
                    return yaml.safe_load(content) or {}
                except yaml.YAMLError as e:
                    raise ValueError(f"Cannot parse file as JSON or YAML: {e}") from e

        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot decode file {file_path}: {e}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}") from e
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}") from e
        except PermissionError as e:
            raise ValueError(f"Cannot read file {file_path}: {e}") from e

    @staticmethod
    def save_variables(file_path: Path, variables: dict[str, Any], format: str = "json") -> None:
        """Save variables to file.

        Args:
        ----
            file_path: Path to save file
            variables: Variables dictionary
            format: Output format ('json' or 'yaml')

        """
        try:
            if format.lower() == "json":
                content = json.dumps(variables, indent=2)
                if file_path.suffix == "":
                    file_path = file_path.with_suffix(".json")
            elif format.lower() in {"yaml", "yml"}:
                content = yaml.safe_dump(variables, default_flow_style=False, indent=2)
                if file_path.suffix == "":
                    file_path = file_path.with_suffix(".yaml")
            else:
                raise ValueError(f"Unsupported format: {format}")

            file_path.write_text(content, encoding="utf-8")

        except PermissionError as e:
            raise ValueError(f"Cannot write file {file_path}: {e}") from e

    @staticmethod
    def validate_variables(variables: dict[str, Any], query: str) -> list[str]:
        """Validate that variables match query requirements.

        Args:
        ----
            variables: Variables dictionary
            query: GraphQL query string

        Returns:
        -------
            List of validation errors (empty if valid)

        """
        errors = []

        try:
            # Parse query to find variable definitions
            parsed = parse(query)

            required_vars = set()
            optional_vars = set()

            for definition in parsed.definitions:
                if hasattr(definition, "variable_definitions") and definition.variable_definitions:
                    for var_def in definition.variable_definitions:
                        var_name = var_def.variable.name.value

                        # Check if variable is required (non-null type without default)
                        is_required = (
                            hasattr(var_def.type, "kind")
                            and var_def.type.kind == "non_null_type"
                            and var_def.default_value is None
                        )

                        if is_required:
                            required_vars.add(var_name)
                        else:
                            optional_vars.add(var_name)

            # Check for missing required variables
            provided_vars = set(variables.keys())
            missing_required = required_vars - provided_vars

            if missing_required:
                errors.append(f"Missing required variables: {', '.join(sorted(missing_required))}")

            # Check for unknown variables
            all_expected_vars = required_vars | optional_vars
            unknown_vars = provided_vars - all_expected_vars

            if unknown_vars:
                errors.append(f"Unknown variables: {', '.join(sorted(unknown_vars))}")

        except Exception as e:
            errors.append(f"Variable validation failed: {e}")

        return errors


class ExportHandler:
    """Handle query and result export operations."""

    @staticmethod
    def export_queries(
        queries: list[dict[str, Any]], output_path: Path, format: str = "json"
    ) -> None:
        """Export queries to file.

        Args:
        ----
            queries: List of query dictionaries
            output_path: Output file path
            format: Export format ('json', 'yaml', 'csv')

        """
        try:
            if format.lower() == "json":
                content = json.dumps(queries, indent=2, default=str)
                if output_path.suffix == "":
                    output_path = output_path.with_suffix(".json")

            elif format.lower() in {"yaml", "yml"}:
                content = yaml.safe_dump(queries, default_flow_style=False, indent=2, default=str)
                if output_path.suffix == "":
                    output_path = output_path.with_suffix(".yaml")

            elif format.lower() == "csv":
                import csv
                import io

                if not queries:
                    content = ""
                else:
                    output = io.StringIO()

                    # Get all possible field names
                    all_fields = set()
                    for query in queries:
                        all_fields.update(query.keys())

                    fields = sorted(all_fields)
                    writer = csv.DictWriter(output, fieldnames=fields)

                    writer.writeheader()
                    for query in queries:
                        # Convert complex values to strings
                        row = {}
                        for field in fields:
                            value = query.get(field, "")
                            if isinstance(value, (dict, list)):
                                row[field] = json.dumps(value)
                            else:
                                row[field] = str(value) if value is not None else ""
                        writer.writerow(row)

                    content = output.getvalue()

                if output_path.suffix == "":
                    output_path = output_path.with_suffix(".csv")

            else:
                raise ValueError(f"Unsupported export format: {format}")

            output_path.write_text(content, encoding="utf-8")

        except PermissionError as e:
            raise ValueError(f"Cannot write file {output_path}: {e}") from e

    @staticmethod
    def import_queries(file_path: Path) -> list[dict[str, Any]]:
        """Import queries from file.

        Args:
        ----
            file_path: Input file path

        Returns:
        -------
            List of query dictionaries

        """
        try:
            content = file_path.read_text(encoding="utf-8")

            if file_path.suffix.lower() == ".json":
                data = json.loads(content)
            elif file_path.suffix.lower() in {".yaml", ".yml"}:
                data = yaml.safe_load(content)
            elif file_path.suffix.lower() == ".csv":
                import csv
                import io

                reader = csv.DictReader(io.StringIO(content))
                data = []
                for row in reader:
                    # Try to parse JSON fields
                    parsed_row = {}
                    for key, value in row.items():
                        if value.strip().startswith(("{", "[")):
                            try:
                                parsed_row[key] = json.loads(value)
                            except json.JSONDecodeError:
                                parsed_row[key] = value
                        else:
                            parsed_row[key] = value
                    data.append(parsed_row)
            else:
                raise ValueError(f"Unsupported import format: {file_path.suffix}")

            # Ensure data is a list
            if not isinstance(data, list):
                data = [data]

            return data

        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot decode file {file_path}: {e}") from e
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Cannot parse file {file_path}: {e}") from e
        except PermissionError as e:
            raise ValueError(f"Cannot read file {file_path}: {e}") from e
