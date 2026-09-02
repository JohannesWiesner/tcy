import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tcy.validate_tsv import (
    ValidationConfigError,
    validate_tsv,
    validate_uppercase_cell_starts,
)


class ValidateUppercaseCellStartsTests(unittest.TestCase):
    def setUp(self):
        self.header = ["package_name", "conda_channel"]
        self.descriptor = {"rules": {"noUppercaseCellStart": True}}
        self.missing_values = {""}

    def test_rejects_uppercase_start_in_any_cell(self):
        rows = [
            {"package_name": "numpy", "conda_channel": "Conda-forge"},
            {"package_name": "Pandas", "conda_channel": "conda-forge"},
        ]

        errors = validate_uppercase_cell_starts(
            self.header, rows, self.descriptor, self.missing_values
        )

        self.assertEqual(
            errors,
            [
                "Row 2, column 'conda_channel': 'Conda-forge' must not start "
                "with an uppercase letter.",
                "Row 3, column 'package_name': 'Pandas' must not start with "
                "an uppercase letter.",
            ],
        )

    def test_allows_lowercase_numeric_and_missing_starts(self):
        rows = [
            {"package_name": "numpy", "conda_channel": "conda-forge"},
            {"package_name": "7zip", "conda_channel": ""},
        ]

        errors = validate_uppercase_cell_starts(
            self.header, rows, self.descriptor, self.missing_values
        )

        self.assertEqual(errors, [])

    def test_disabled_rule_does_not_reject_uppercase_start(self):
        rows = [{"package_name": "NumPy", "conda_channel": "conda-forge"}]
        descriptor = {"rules": {"noUppercaseCellStart": False}}

        errors = validate_uppercase_cell_starts(
            self.header, rows, descriptor, self.missing_values
        )

        self.assertEqual(errors, [])

    def test_rule_must_be_boolean(self):
        descriptor = {"rules": {"noUppercaseCellStart": "true"}}

        with self.assertRaisesRegex(
            ValidationConfigError,
            "rules.noUppercaseCellStart must be boolean",
        ):
            validate_uppercase_cell_starts(
                self.header, [], descriptor, self.missing_values
            )

    def test_default_descriptor_rejects_capitalized_conda_channel(self):
        contents = (
            "package_name\tversion\tpackage_manager\tconda_channel\tinclude\t"
            "language\tbug_flag\n"
            "numpy\t\tconda\tConda-forge\ttrue\tpython\t\n"
        )
        descriptor = Path(__file__).parents[1] / "tcy" / "packages.validation.yml"

        with TemporaryDirectory() as directory:
            tsv = Path(directory) / "packages.tsv"
            tsv.write_text(contents, encoding="utf-8")

            errors = validate_tsv(tsv, descriptor)

        self.assertIn(
            "Row 2, column 'conda_channel': 'Conda-forge' must not start with "
            "an uppercase letter.",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
