# TCY  

<img  src="assets/logo_tcy_transparent_background.png"
      alt="tcy logo"
      width="100">

`TCY` (**T**sv → **C**onda **Y**ML) is a lightweight tool for generating reproducible Conda environment `.yml` files from `.tsv` (spreadsheet-style) input files. Instead of maintaining opaque YAML files, TCY lets you **document the why, what, and where** of every package—while still producing Conda-ready environment definitions.

---

## Why TCY?

Conda environment files are great for reproducibility, but they have limitations:

- ❓ *Why* was a package included?
- 📦 *What* does it do?
- 🖥️ Does it work on Linux, macOS, and Windows or only on specific platforms?
- ⚠️ Are there known (platform-specific) bugs?

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

## Customizing `packages.validation.yml`

Validation of `packages.tsv` is controlled by `packages.validation.yml`.

The file has two main sections:

* `schema`: defines the expected columns, their types, required values, and allowed values.
* `rules`: defines additional checks such as column order, dependencies, and whitespace validation.

| Setting                         | What it does                                                                                     | Example                                |
| ------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------- |
| `missingValues`                 | Defines values that count as missing.                                                            | `[""]` means an empty cell is missing. |
| `fields[].name`                 | Defines a column that must exist in the TSV.                                                     | `name: package_name`                   |
| `fields[].type`                 | Defines the expected data type.                                                                  | `type: string`, `type: boolean`        |
| `constraints.required`          | Requires every row to contain a value in this column.                                            | `required: true`                       |
| `constraints.enum`              | Restricts non-empty cells to specific values.                                                    | `enum: [conda, pip, cran]`             |
| `trueValues` / `falseValues`    | Defines accepted representations of boolean values.                                              | `trueValues: ["true"]`                 |
| `noLeadingOrTrailingWhitespace` | Rejects leading or trailing whitespace in all cells and column names.                            | `true`                                 |
| `noUppercaseCellStart`          | Rejects non-missing cells whose first character is an uppercase letter.                          | `true`                                 |
| `columns.requireOrder`          | Requires schema-defined columns to occur in the same relative order as in `fields`.              | `true`                                 |
| `columns.allowAdditional`       | Allows columns that are not listed under `fields`.                                               | `true`                                 |
| `columnDependencies`            | Requires other columns when a particular column is filled.                                       | See example below.                     |
| `conditionalColumnDependencies` | Requires other columns when a particular column has a specific value.                            | See example below.                     |
| `multiOptionColumns`            | Allows multiple separator-delimited values in one cell and restricts them to predefined options. | See example below.                     |

### Column dependencies

Use `columnDependencies` when filling one column should require another column to be filled as well.

```yaml
columnDependencies:
  version:
    - package_name
```

This means:

> If `version` is filled, `package_name` must also be filled.

Multiple required columns can be specified:

```yaml
columnDependencies:
  version:
    - package_name
    - package_manager
```

If no such dependencies are needed, use:

```yaml
columnDependencies: {}
```

### Conditional column dependencies

Use `conditionalColumnDependencies` when another column should only be required for a specific value.

```yaml
conditionalColumnDependencies:
  package_manager:
    conda:
      - conda_channel
```

This means:

> If `package_manager` is `conda`, `conda_channel` must be filled.

### Multi-option columns

Use `multiOptionColumns` if one cell may contain several values separated by a delimiter.

```yaml
multiOptionColumns:
  bug_flag:
    separator: ","
    stripItems: false
    unique: true
    options:
      - linux
      - windows
      - cross-platform
```

With this configuration:

```text
linux
linux,windows
linux,windows,cross-platform
```

are valid, while:

```text
linux,macos
linux,linux
```

are invalid.

The options mean:

* `separator`: character used to separate values.
* `stripItems`: whether whitespace around individual values should be removed before validation.
* `unique`: whether the same option may appear more than once.
* `options`: list of allowed values.

If no multi-option columns are needed, use:

```yaml
multiOptionColumns: {}
```

### Example field definitions

A required column:

```yaml
- name: package_name
  type: string
  constraints:
    required: true
```

An optional column with restricted values:

```yaml
- name: bug_flag
  type: string
  constraints:
    enum:
      - linux
      - windows
      - cross-platform
```

Here, an empty `bug_flag` is allowed, but a non-empty value must be one of the listed options.

---

## CRAN Packages (Experimental)

Some R packages are not available via Conda.

TCY can generate an `install_cran_packages.sh` script that should:
1. Activate the Conda environment
2. Start R
3. Install CRAN packages inside this environment using `install.packages()`

</details>
