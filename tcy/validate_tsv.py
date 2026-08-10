#!/usr/bin/env python3
"""
Validate a TSV file using a YAML validation descriptor.

Install:
    python -m pip install "frictionless>=5,<6" pyyaml

Usage:
    python validate_tsv.py packages.tsv packages.validation.yml

Exit codes:
    0 = valid
    1 = invalid TSV
    2 = invalid validator configuration / usage
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import yaml
from frictionless import Resource, Schema


class ValidationConfigError(ValueError):
    """Raised when the validation descriptor is invalid."""

def load_descriptor(path: Path) -> dict[str, Any]:
    """Load and validate the basic structure of a YAML validation descriptor.

        Args:
            path: Path to the YAML validation file.

        Returns:
            The parsed validation descriptor.

        Raises:
            ValidationConfigError: If the file cannot be loaded or its required
                schema structure is invalid.
        """
    try:
        with path.open(encoding="utf-8") as file:
            descriptor = yaml.safe_load(file)
    except (OSError, yaml.YAMLError) as exc:
        raise ValidationConfigError(
            f"Could not load validation descriptor {path}: {exc}"
        ) from exc

    if not isinstance(descriptor, dict):
        raise ValidationConfigError("Validation descriptor must be a YAML mapping.")

    schema = descriptor.get("schema")
    if not isinstance(schema, dict):
        raise ValidationConfigError("Validation descriptor must contain a 'schema' mapping.")

    fields = schema.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ValidationConfigError("schema.fields must be a non-empty list.")

    if any(
        not isinstance(field, dict) or not isinstance(field.get("name"), str)
        for field in fields
    ):
        raise ValidationConfigError(
            "Every schema field must contain a string 'name'."
        )

    return descriptor

def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str | None]]]:
    """Read a TSV file without converting its cell values.

        Args:
            path: Path to the TSV file.

        Returns:
            A tuple containing the column names and all rows as dictionaries.

        Raises:
            ValueError: If the TSV file cannot be read or parsed.
        """
    try:
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file, delimiter="\t", strict=True)
            return list(reader.fieldnames or []), list(reader)
    except (OSError, csv.Error, UnicodeError) as exc:
        raise ValueError(f"Could not parse TSV file: {exc}") from exc

def validate_columns(
    header: list[str],
    descriptor: dict[str, Any],
) -> list[str]:
    """Validate required columns, additional columns, and column order.

        Args:
            header: Column names found in the TSV file.
            descriptor: Parsed validation descriptor.

        Returns:
            Human-readable validation errors. An empty list means the check passed.

        Raises:
            ValidationConfigError: If the column rules are malformed.
        """
    expected = [field["name"] for field in descriptor["schema"]["fields"]]
    rules = descriptor.get("rules", {}).get("columns", {})

    if not isinstance(rules, dict):
        raise ValidationConfigError("rules.columns must be a mapping.")

    allow_additional = rules.get("allowAdditional", False)
    require_order = rules.get("requireOrder", True)

    if not isinstance(allow_additional, bool):
        raise ValidationConfigError(
            "rules.columns.allowAdditional must be boolean."
        )
    if not isinstance(require_order, bool):
        raise ValidationConfigError(
            "rules.columns.requireOrder must be boolean."
        )

    errors = []

    missing = [column for column in expected if column not in header]
    if missing:
        errors.append(f"Missing required columns: {missing!r}.")

    if not allow_additional:
        additional = [column for column in header if column not in expected]
        if additional:
            errors.append(f"Unexpected additional columns: {additional!r}.")

    if require_order and not missing:
        required_in_file = [column for column in header if column in expected]
        if required_in_file != expected:
            errors.append(
                "Required columns are in the wrong order: "
                f"expected {expected!r}, found {required_in_file!r}."
            )

    return errors

def validate_whitespace(
    header: list[str],
    rows: list[dict[str, str | None]],
    descriptor: dict[str, Any],
    missing_values: set[str],
) -> list[str]:
    """Check all headers and cells for leading or trailing whitespace.

        Missing values are ignored. The check is only performed when
        ``noLeadingOrTrailingWhitespace`` is enabled in the validation rules.

        Args:
            header: Column names found in the TSV file.
            rows: Raw TSV rows.
            descriptor: Parsed validation descriptor.
            missing_values: Values that represent missing cells.

        Returns:
            Human-readable validation errors. An empty list means the check passed.

        Raises:
            ValidationConfigError: If the whitespace rule is not boolean.
        """
    enabled = descriptor.get("rules", {}).get(
        "noLeadingOrTrailingWhitespace",
        False,
    )
    if not isinstance(enabled, bool):
        raise ValidationConfigError(
            "rules.noLeadingOrTrailingWhitespace must be boolean."
        )
    if not enabled:
        return []

    errors = []

    for index, column in enumerate(header, start=1):
        if column != column.strip():
            errors.append(
                f"Header column {index}: {column!r} has leading or trailing whitespace."
            )

    for row_number, row in enumerate(rows, start=2):
        for column in header:
            value = row.get(column)
            if value is None or value in missing_values:
                continue
            if value != value.strip():
                errors.append(
                    f"Row {row_number}, column {column!r}: "
                    f"{value!r} has leading or trailing whitespace."
                )

    return errors

def validate_schema(
    rows: list[dict[str, str | None]],
    descriptor: dict[str, Any],
) -> list[str]:
    """Validate schema-defined columns with Frictionless.

        Only columns declared in ``schema.fields`` are passed to Frictionless, so
        additional TSV columns can be allowed independently by the column rules.

        Args:
            rows: Raw TSV rows.
            descriptor: Parsed validation descriptor.

        Returns:
            Human-readable Frictionless validation errors.
        """
    columns = [field["name"] for field in descriptor["schema"]["fields"]]
    data = [columns]

    for row in rows:
        data.append([row.get(column) or "" for column in columns])

    resource = Resource(
        data=data,
        schema=Schema.from_descriptor(descriptor["schema"]),
    )
    report = resource.validate()

    return [message for [message] in report.flatten(["message"])]

def validate_dependencies(
    rows: list[dict[str, str | None]],
    descriptor: dict[str, Any],
    missing_values: set[str],
) -> list[str]:
    """Validate unconditional and conditional column dependencies.

        Args:
            rows: Raw TSV rows.
            descriptor: Parsed validation descriptor.
            missing_values: Values that represent missing cells.

        Returns:
            Human-readable validation errors. An empty list means the check passed.

        Raises:
            ValidationConfigError: If dependency rules are malformed.
        """
    rules = descriptor.get("rules", {})
    errors = []

    def is_filled(value: str | None) -> bool:
        return value is not None and value not in missing_values

    dependencies = rules.get("columnDependencies", {})
    if not isinstance(dependencies, dict):
        raise ValidationConfigError("rules.columnDependencies must be a mapping.")

    for trigger, required_columns in dependencies.items():
        if not isinstance(required_columns, list):
            raise ValidationConfigError(
                f"Dependency for {trigger!r} must be a list."
            )

        for row_number, row in enumerate(rows, start=2):
            if not is_filled(row.get(trigger)):
                continue

            for required in required_columns:
                if not is_filled(row.get(required)):
                    errors.append(
                        f"Row {row_number}: {required!r} must be filled "
                        f"when {trigger!r} is filled."
                    )

    conditional = rules.get("conditionalColumnDependencies", {})
    if not isinstance(conditional, dict):
        raise ValidationConfigError(
            "rules.conditionalColumnDependencies must be a mapping."
        )

    for trigger, conditions in conditional.items():
        if not isinstance(conditions, dict):
            raise ValidationConfigError(
                f"Conditions for {trigger!r} must be a mapping."
            )

        for trigger_value, required_columns in conditions.items():
            if not isinstance(required_columns, list):
                raise ValidationConfigError(
                    f"Conditional dependency for "
                    f"{trigger!r}={trigger_value!r} must be a list."
                )

            for row_number, row in enumerate(rows, start=2):
                if row.get(trigger) != str(trigger_value):
                    continue

                for required in required_columns:
                    if not is_filled(row.get(required)):
                        errors.append(
                            f"Row {row_number}: {required!r} must be filled "
                            f"when {trigger!r} is {str(trigger_value)!r}."
                        )

    return errors

def validate_multi_option_columns(
    rows: list[dict[str, str | None]],
    descriptor: dict[str, Any],
    missing_values: set[str],
) -> list[str]:
    """Validate columns that may contain multiple delimited options.

        Each configured cell is split using its separator and every resulting item
        must be one of the configured options. Duplicate items can optionally be
        rejected.

        Args:
            rows: Raw TSV rows.
            descriptor: Parsed validation descriptor.
            missing_values: Values that represent missing cells.

        Returns:
            Human-readable validation errors. An empty list means the check passed.

        Raises:
            ValidationConfigError: If a multi-option rule is malformed.
        """
    configs = descriptor.get("rules", {}).get("multiOptionColumns", {})
    if not isinstance(configs, dict):
        raise ValidationConfigError(
            "rules.multiOptionColumns must be a mapping."
        )

    errors = []

    for column, config in configs.items():
        if not isinstance(config, dict):
            raise ValidationConfigError(
                f"Multi-option configuration for {column!r} must be a mapping."
            )

        separator = config.get("separator", ",")
        strip_items = config.get("stripItems", False)
        unique = config.get("unique", False)
        options = config.get("options", [])

        if not isinstance(separator, str) or not separator:
            raise ValidationConfigError(
                f"Separator for {column!r} must be a non-empty string."
            )
        if not isinstance(strip_items, bool):
            raise ValidationConfigError(
                f"stripItems for {column!r} must be boolean."
            )
        if not isinstance(unique, bool):
            raise ValidationConfigError(
                f"unique for {column!r} must be boolean."
            )
        if not isinstance(options, list) or not all(
            isinstance(option, str) for option in options
        ):
            raise ValidationConfigError(
                f"options for {column!r} must be a list of strings."
            )

        allowed = set(options)

        for row_number, row in enumerate(rows, start=2):
            value = row.get(column)
            if value is None or value in missing_values:
                continue

            items = value.split(separator)
            if strip_items:
                items = [item.strip() for item in items]

            invalid = [item for item in items if item not in allowed]
            if invalid:
                errors.append(
                    f"Row {row_number}, column {column!r}: "
                    f"invalid option(s) {invalid!r}; allowed options are {options!r}."
                )

            if unique and len(items) != len(set(items)):
                errors.append(
                    f"Row {row_number}, column {column!r}: options must be unique."
                )

    return errors

def validate_tsv(
    tsv_path: str | Path,
    validation_path: str | Path,
) -> list[str]:
    """Validate a TSV file against a YAML validation descriptor.

        This runs the custom whitespace, column, dependency, and multi-option
        checks together with the Frictionless schema validation.

        Args:
            tsv_path: Path to the TSV file to validate.
            validation_path: Path to the YAML validation descriptor.

        Returns:
            Human-readable validation errors. An empty list means the TSV is valid.

        Raises:
            ValidationConfigError: If the validation descriptor is malformed.
        """
    tsv_path = Path(tsv_path)
    if not tsv_path.is_file():
        return [f"TSV file does not exist: {tsv_path}"]

    descriptor = load_descriptor(Path(validation_path))

    try:
        header, rows = read_tsv(tsv_path)
    except ValueError as exc:
        return [str(exc)]

    schema = descriptor["schema"]
    missing_values = set(schema.get("missingValues", [""]))
    if not all(isinstance(value, str) for value in missing_values):
        raise ValidationConfigError(
            "schema.missingValues must be a list of strings."
        )

    errors = []
    errors.extend(validate_whitespace(header, rows, descriptor, missing_values))
    errors.extend(validate_columns(header, descriptor))

    required_columns = [field["name"] for field in schema["fields"]]
    if all(column in header for column in required_columns):
        errors.extend(validate_schema(rows, descriptor))

    errors.extend(validate_dependencies(rows, descriptor, missing_values))
    errors.extend(
        validate_multi_option_columns(rows, descriptor, missing_values)
    )

    return list(dict.fromkeys(errors))

def main() -> int:
    """Run the command-line validator and return its process exit code.

        Returns:
            ``0`` if the TSV is valid, ``1`` if validation fails, or ``2`` if
            validation cannot be performed.
        """
    parser = argparse.ArgumentParser(description="Validate a TSV file using a YAML validation descriptor.")
    parser.add_argument("tsv", type=Path, help="TSV file to validate")
    parser.add_argument("validation",type=Path,help="YAML file describing the validation rules")
    args = parser.parse_args()

    try:
        errors = validate_tsv(args.tsv, args.validation)
    except Exception as exc:
        print(f"Validation could not be performed: {exc}", file=sys.stderr)
        return 2

    if errors:
        print(f"INVALID: {args.tsv}")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"VALID: {args.tsv}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
