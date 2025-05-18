![GitHub all releases](https://img.shields.io/github/downloads/mcasari/release-handler/total)
![GitHub language count](https://img.shields.io/github/languages/count/mcasari/release-handler)
![GitHub top language](https://img.shields.io/github/languages/top/mcasari/release-handler?color=yellow)
![Bitbucket open issues](https://img.shields.io/bitbucket/issues/mcasari/release-handler)
![GitHub forks](https://img.shields.io/github/forks/mcasari/release-handler?style=social)
![GitHub Repo stars](https://img.shields.io/github/stars/mcasari/release-handler?style=social)



# 📚 Public Functions in `release_handler.py`

The script provides automation for handling project versioning, tagging, and Git operations across multiple project types (Maven, Angular, Ant). Below are the main publicly available functions that can be called directly or used via CLI:

## `update_versions(project_filter='')`
Updates the version numbers of all projects (or a filtered project) according to the configuration in `release_handler_config.yaml`.

- 💡 Supports Maven (`pom.xml`), Angular (`package.json`), and Ant (`version.properties`) projects.
- ⚙️ Clones the project repository and updates properties and dependencies.
- 📝 Prompts to commit the version changes.

---

## `update_tags(project_filter='')`
Creates Git tags for projects based on configurations.

- 🏷️ Tags the project with a specified value, optionally appending a progressive suffix.
- 🧪 Checks if the tag exists and pushes it to the remote if it does not.

---

## `push_changes(project_filter='')`
Pushes committed changes to the remote repository after optional compilation checks.

- ✅ Detects unpushed commits.
- 🔍 Offers to compile the project before pushing (based on project type).
- ⬆️ Pushes changes to the remote only if confirmed.

---

## `extract_git_info_to_excel(project_filter='', output_file="git_info.xlsx")`
Extracts Git information from all configured repositories and exports it into a formatted Excel file.

- 📊 Includes remote URL, last commit info, tags, and branches.
- 🖨️ Automatically adjusts column widths and applies header formatting.

---

# ⚙️ Usage via CLI

You can invoke this script from the command line with:

```bash
python release_handler.py <command> [project_name]
```

## Available Commands:
- `update_versions` – Updates version numbers.
- `update_tags` – Tags the repository.
- `push_changes` – Pushes committed changes.
- `extract_git_info_to_excel` – Exports Git metadata to Excel.

## Example:
```bash
python release_handler.py update_versions my-project
```


