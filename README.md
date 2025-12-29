# TCY  
**T**sv → **C**onda **Y**ML

`TCY` is a lightweight tool for generating reproducible Conda environment `.yml` files from a documented `.tsv` (spreadsheet-style) input file. Instead of maintaining opaque YAML files, TCY lets you **document the why, what, and where** of every package—while still producing Conda-ready environment definitions.

---

## Why TCY?

Conda environment files are great for reproducibility, but they have limitations:

- ❓ *Why* was a package included?
- 📦 *What* does it do?
- 🖥️ Does it work on Linux, macOS, and Windows?
- ⚠️ Are there known platform-specific bugs?

Spreadsheet formats (like `.tsv`) are much better for documentation, annotations, and validation.   **TCY bridges this gap** by letting you maintain a richly documented package list and exporting it into valid Conda `.yml` files.

---

## Recommended Workflow (Using This Repository as a Template)

The easiest way to use TCY is to create your own repository **from this template**.

### Why use the template?

1. Your package documentation lives in a GitHub repository and is accessible from anywhere.
2. Conda environment solving can be slow. This workflow offloads that work to GitHub Actions, producing **pre-solved environment files** that you can create locally in seconds.

---

### Step-by-Step Setup

1. **Create a new repository**  
   Click **“Use this template”** in the upper right of this repository.

2. **Allow GitHub Actions to push changes**  
   Go to:  
   `Settings → Actions → General → Workflow permissions`  
   Enable **“Read and write permissions”**.

3. **Clone your repository locally**

4. **Edit the package list**  
   Modify `environments/packages.tsv`.

5. **Push your changes**  
   This triggers a GitHub Actions workflow that validates the TSV file and generates OS-specific solved `.yml` files.

6. **Pull the generated files**

7. **Create your Conda environment**
   ```bash
   conda env create -f ubuntu-latest_solved.yml
   ```

---

## What goes into the `packages.tsv` file?

The input spreadsheet file must contain the following columns:

| Column name | Description |
|------------|-------------|
| `package_name` | The official name of the package. |
| `version` | May be left empty, or may specify the package version using the [package match specification syntax](https://docs.conda.io/projects/conda-build/en/latest/resources/package-spec.html#package-match-specifications). |
| `package_manager` | Must be one of: `pip`, `conda`, or `cran`. |
| `conda_channel` | May be left empty if the package manager is `pip` or `cran`, but must contain the name of the conda channel to install from if the package manager is `conda`. |
| `include` | Must be either `true` or `false`. |
| `language` | Must be one of: `python`, `r`, or `julia`. |
| `bug_flag` | May be left empty, or must be one of: `linux`, `windows`, or `cross_platform`. |


---

## 🛠️🛠️ Only For Developers 🛠️🛠️

### Installation

```bash
pip install tcy
```

TCY can be used both as a **Python library** and a **command-line application**.

---

### Using TCY as a Python Library

```python
from tcy import run
```

The `run` function allows you to generate Conda `.yml` files programmatically inside your own codebase.

---

### Using TCY as a Command-Line Application

```bash
tcy {linux|windows} [OPTIONS]
```

#### Required positional argument

- `{linux,windows}`  
  Target operating system for which the environment file is generated.  
  Packages flagged as incompatible with this OS are excluded.  
  Packages flagged as `cross_platform` are never included.

---

#### CLI Options

| Option | Description |
|------|-------------|
| `--yml_name` | Sets the `name:` field in the `.yml` file |
| `--yml_file_name` | Output filename (default: `environment.yml`) |
| `--pip_requirements_file` | Write pip packages to `requirements.txt` |
| `--write_conda_channels` | Inline channels (e.g. `conda-forge::numpy`) |
| `--tsv_path` | Path to `.tsv` file (default: `packages.tsv`) |
| `--yml_dir` | Output directory |
| `--cran_installation_script` | Generate `install_cran_packages.sh` |
| `--cran_mirror` | CRAN mirror URL (default: https://cloud.r-project.org) |
| `--languages` | Filter by `python`, `r`, `julia`, or `all` |

---

## Automatic Validation of `packages.tsv`

This repository includes a testing pipeline that checks the integrity of, and the validity of entries in, the `packages.tsv` file.   Which tests are executed is determined by the `test_configs.json` file. Each test corresponds to a key in this JSON file. If the corresponding value is set to `null`, the test is not executed.

Below is an explanation of each test and the rules for how the values should be provided if the test is enabled.

| key                             | value                                                              | description                                                                                              |
|---------------------------------|--------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| `valid_columns`                 | list of column names                                               | The TSV file must contain only these columns, and they must appear in this exact order.                  |
| `filled_out_columns`            | list of column names                                               | Cells in these columns must not contain NaN values; every row in these columns must contain a value.    |
| `valid_options`                 | dict with column names as keys and lists of valid options as values| Cells in these columns must contain only the one the specified valid options.                                    |
| `column_dependencies`           | dict with column names as keys and lists of other columns as values| If a cell in this column is filled, the corresponding cells in the specified other column(s) must also be filled. |
| `conditional_column_dependencies` | dict of dicts of lists                                           | If a cell in this column has a specific value, the corresponding cells in the specified other column(s) must be filled. |
| `multi_option_columns`          | dict with column names as keys and lists of valid options as values| Cells in these columns must contain only a set of these valid options, separated by commas.                             |

---

## CRAN Packages (Experimental)

Some R packages are not available via Conda.

TCY can generate an `install_cran_packages.sh` script that should:
1. Activate the Conda environment
2. Start R
3. Install CRAN packages inside this environment using `install.packages()`
