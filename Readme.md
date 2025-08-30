# pyrest

A Python command-line REST API client with interactive shell, configuration, aliases, variables, piping, output redirection, and JMESPath post-processing.

---

## Features

- **Interactive Shell:** Command history, editing, and graceful exit.
- **Configuration Management:** Store multiple endpoints in `.pyrest.conf`.
- **REST Commands:** Supports GET, POST, PUT, PATCH, DELETE.
- **Aliases & Variables:** Define shortcuts and session variables.
- **Templates:** Use placeholders in aliases for dynamic substitution.
- **Output Formatting:** Pretty-prints JSON responses.
- **JMESPath Post-Processing:** Filter/transform results with `--jql`.
- **Piping & Redirection:** Pipe output to shell commands or files.
- **Dry Run:** Preview REST call details without executing.

---

## Installation

1. Clone this repo and enter the folder:
    ```sh
    git clone <repo-url>
    cd pyrest
    ```

2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. (Optional) Install as CLI:
    ```sh
    pip install -e .
    ```

---

## Configuration

Create a `.pyrest.conf` file in your home directory or project folder:

```ini
[default]
base_url = https://jsonplaceholder.typicode.com
headers = {}
timeout = 10

[myapi]
base_url = https://reqres.in/api/
timeout = 10

[variables]
user_id = 2
token = abc123

[aliases]
get_user = use myapi; GET /users/{0}
get_posts = use default; GET /posts/{0}
```

---

## Usage

Start the shell:
```sh
python main.py
```
or, if installed as CLI:
```sh
pyrest
```

### Example Commands

- **GET request:**
    ```
    pyrest> GET /posts/1
    ```

- **POST request:**
    ```
    pyrest> POST /posts '{"title": "foo", "body": "bar", "userId": 1}'
    ```

- **Alias with argument:**
    ```
    pyrest> get_user 5
    ```

- **Variable substitution:**
    ```
    pyrest> set user_id = 3
    pyrest> GET /users/$user_id
    ```

- **JMESPath post-processing:**
    ```
    pyrest> GET /posts/1 --jql "title"
    ```

- **Dry run:**
    ```
    pyrest> dry GET /posts/1
    pyrest> dry get_user 5
    ```

- **Output redirection:**
    ```
    pyrest> GET /posts/1 > post1.json
    ```

- **Piping:**
    ```
    pyrest> GET /posts | jq '.[] | select(.userId == 1)'
    ```

---

## Advanced

- **Multiple endpoints:** Switch with `use endpoint_name`.
- **Aliases:** Use `{0}`, `{1}` in alias definitions for argument substitution.
- **Certificates:** Add `cert` and `key` in endpoint config for HTTPS client auth.

---

## Help

Type `help` in the shell for a full command list.

---

## Requirements

- Python 3.7+
- requests
- prompt_toolkit
- jmespath