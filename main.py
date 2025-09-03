import os
import sys
import json
import shlex
import subprocess
import configparser
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from rest_client import RestClient
import jmespath

CONFIG_PATH = os.path.expanduser("~/.pyrest.conf")

class RESTCLI:
    def __init__(self, config_file=CONFIG_PATH):
        self.config_file = config_file
        print (self.config_file)
        print (CONFIG_PATH)
        
        self.variables = {}
        self.aliases = {}
        self.configs = self.load_config(config_file)
        self.current_endpoint = list(self.configs.keys())[0] if self.configs else None
        self.rest_client = None
        self.set_endpoint(self.current_endpoint)
        self.session = PromptSession(history=FileHistory(os.path.expanduser("~/.pyrest_history")))
        self.commands = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'set', 'alias', 'use', 'show', 'exit', 'help']
        self.completer = WordCompleter(self.commands, ignore_case=True)

    def load_config(self, config_file):
        configs = {}
        variables = {}
        aliases = {}
        parser = configparser.ConfigParser()

        # Step 1: Check for [source] section in main config
        if os.path.exists(config_file):
            parser.read(config_file)
            source_files = []
            for section in parser.sections():
                if section.lower() == "source":
                    for k, v in parser.items(section):
                        if k == "file":
                            source_files.append(v)
        # Step 2: Load each source file first
            for src_file in source_files:
                src_file_path = os.path.expanduser(src_file)
                if os.path.exists(src_file_path):
                    src_parser = configparser.ConfigParser()
                    src_parser.read(src_file_path)
                    # Load variables from source
                    for section in src_parser.sections():
                        if section.lower() == "variables":
                            for k, v in src_parser.items(section):
                                variables[k] = v
                    # Load aliases from source
                    for section in src_parser.sections():
                        if section.lower() == "aliases":
                            for k, v in src_parser.items(section):
                                for var_k, var_v in variables.items():
                                    v = v.replace(f"${var_k}", str(var_v))
                                aliases[k] = v
                    # Load endpoint configs from source
                    for section in src_parser.sections():
                        if section.lower() not in ["variables", "aliases", "source"]:
                            base_url = src_parser.get(section, 'base_url', fallback='')
                            headers = src_parser.get(section, 'headers', fallback='{}')
                            timeout = src_parser.get(section, 'timeout', fallback='10')
                            cert = src_parser.get(section, 'cert', fallback=None)
                            key = src_parser.get(section, 'key', fallback=None)
                            for var_k, var_v in variables.items():
                                base_url = base_url.replace(f"${var_k}", str(var_v))
                                headers = headers.replace(f"${var_k}", str(var_v))
                                timeout = timeout.replace(f"${var_k}", str(var_v))
                                if cert:
                                    cert = cert.replace(f"${var_k}", str(var_v))
                                if key:
                                    key = key.replace(f"${var_k}", str(var_v))
                            configs[section] = {
                                'base_url': base_url,
                                'headers': json.loads(headers),
                                'timeout': int(timeout),
                                'cert': cert,
                                'key': key
                            }
        # Step 3: Now load main config (overrides source)
        # (parser already read above)
            for section in parser.sections():
                if section.lower() == "variables":
                    for k, v in parser.items(section):
                        variables[k] = v
                elif section.lower() == "aliases":
                    for k, v in parser.items(section):
                        for var_k, var_v in variables.items():
                            v = v.replace(f"${var_k}", str(var_v))
                        aliases[k] = v
                elif section.lower() == "source":
                    continue
                else:
                    base_url = parser.get(section, 'base_url', fallback='')
                    headers = parser.get(section, 'headers', fallback='{}')
                    timeout = parser.get(section, 'timeout', fallback='10')
                    cert = parser.get(section, 'cert', fallback=None)
                    key = parser.get(section, 'key', fallback=None)
                    for var_k, var_v in variables.items():
                        base_url = base_url.replace(f"${var_k}", str(var_v))
                        headers = headers.replace(f"${var_k}", str(var_v))
                        timeout = timeout.replace(f"${var_k}", str(var_v))
                        if cert:
                            cert = cert.replace(f"${var_k}", str(var_v))
                        if key:
                            key = key.replace(f"${var_k}", str(var_v))
                    configs[section] = {
                        'base_url': base_url,
                        'headers': json.loads(headers),
                        'timeout': int(timeout),
                        'cert': cert,
                        'key': key
                    }
        self.variables = variables
        self.aliases = aliases
        return configs

    def set_endpoint(self, endpoint):
        if endpoint and endpoint in self.configs:
            cfg = self.configs[endpoint]
            class Config: pass
            config = Config()
            config.base_url = cfg['base_url']
            config.headers = cfg['headers']
            config.timeout = cfg['timeout']
            self.rest_client = RestClient(config)
            self.current_endpoint = endpoint

    def substitute_vars(self, text):
        for k, v in self.variables.items():
            text = text.replace(f"${k}", str(v))
        return text

    def parse_json(self, data):
        # Support @filename to inject JSON from file
        if isinstance(data, str) and data.startswith('@'):
            filename = data[1:]
            print(filename)
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to read JSON from {filename}: {e}")
                return None
        try:
            return json.loads(data)
        except Exception:
            return data

    def pretty_print(self, resp, status=None, jql_query=None):
        if resp is None:
            print("No response.")
            return
        if status:
            print(f"HTTP {status}")
        # JQL post-processing if query is provided
        if jql_query:
            try:
                filtered = jmespath.search(jql_query, resp)
                print(json.dumps(filtered, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"JMESPath query failed: {e}")
        else:
            print(json.dumps(resp, indent=2, ensure_ascii=False))

    def run(self):
        print(f"Welcome to pyrest. Current endpoint: {self.current_endpoint}")
        while True:
            try:
                line = self.session.prompt('pyrest> ', completer=self.completer)
                line = line.strip()
                if not line:
                    continue
                # Parse for optional JQL query: syntax --jql "query"
                jql_query = None
                if '--jql' in line:
                    parts = shlex.split(line)
                    if '--jql' in parts:
                        idx = parts.index('--jql')
                        if idx + 1 < len(parts):
                            jql_query = parts[idx + 1]
                            # Remove --jql and query from line
                            parts = parts[:idx] + parts[idx+2:]
                            line = ' '.join(parts)
                # Start with all commands from the input line
                command_queue = [cmd.strip() for cmd in line.split(';') if cmd.strip()]
                while command_queue:
                    cmd_line = command_queue.pop(0)
                    dry_run = False
                    if cmd_line.lower().startswith('dry '):
                        dry_run = True
                        cmd_line = cmd_line[4:].strip()
                    expanded = False
                    for alias, cmd in self.aliases.items():
                        if cmd_line.lower().startswith(alias.lower()):
                            # Get extra arguments after the alias
                            extra_args = cmd_line[len(alias):].strip()
                            extra_args_list = shlex.split(extra_args)
                            # Substitute placeholders {0}, {1}, ... in the alias command
                            def substitute_placeholders(template, args):
                                for i, arg in enumerate(args):
                                    template = template.replace(f'{{{i}}}', arg)
                                return template
                            expanded_cmd = substitute_placeholders(cmd, extra_args_list)
                            # Split expanded command into sub-commands and add to queue
                            expanded_cmds = [c.strip() for c in expanded_cmd.split(';') if c.strip()]
                            if dry_run:
                                for ecmd in expanded_cmds:
                                    self.show_dry_run(self.substitute_vars(ecmd))
                                expanded = True
                                break
                            else:
                                command_queue = expanded_cmds + command_queue
                                expanded = True
                                break
                    if expanded:
                        continue
                    # Variable substitution
                    cmd_line = self.substitute_vars(cmd_line)
                    if dry_run:
                        self.show_dry_run(cmd_line)
                        continue
                    # Handle exit
                    if cmd_line.lower() in ['exit', 'quit']:
                        print("Bye!")
                        return
                    # Handle help
                    if cmd_line.lower() == 'help':
                        self.show_help()
                        continue
                    # Show endpoints
                    if cmd_line == 'show endpoints':
                        print("Configured endpoints:")
                        for ep in self.configs:
                            print(f"  {ep}")
                        continue
                    # Show variables
                    if cmd_line == 'show vars':
                        print("Session variables:")
                        for k, v in self.variables.items():
                            print(f"  {k} = {v}")
                        continue
                    # Set variable
                    if cmd_line.startswith('set '):
                        parts = cmd_line[4:].split('=', 1)
                        if len(parts) == 2:
                            k, v = parts[0].strip(), parts[1].strip()
                            self.variables[k] = v
                            print(f"Set {k} = {v}")
                        continue
                    # Alias definition
                    if cmd_line.startswith('alias '):
                        parts = cmd_line[6:].split('=', 1)
                        if len(parts) == 2:
                            k, v = parts[0].strip(), parts[1].strip()
                            self.aliases[k] = v
                            print(f"Alias {k} = {v}")
                        continue
                    # Handle endpoint switching
                    if cmd_line.startswith('use '):
                        ep = cmd_line.split(' ', 1)[1].strip()
                        if ep in self.configs:
                            self.set_endpoint(ep)
                            print(f"Switched to endpoint: {ep}")
                        else:
                            print(f"Endpoint '{ep}' not found.")
                        continue
                    # Handle piping and redirection
                    if '|' in cmd_line or '>' in cmd_line:
                        if dry_run:
                            self.show_dry_run(cmd_line)
                        else:
                            self.handle_pipe_redirect(cmd_line)
                        continue
                    # Parse REST commands
                    if dry_run:
                        self.show_dry_run(cmd_line)
                    else:
                        self.handle_rest_command(cmd_line, jql_query)
            except KeyboardInterrupt:
                print("\nBye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    def handle_rest_command(self, line, jql_query=None):
        print(line)
        parts = shlex.split(line)
        if not parts:
            return
        cmd = parts[0].upper()
        if cmd not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            print(f"Unknown command: {cmd}")
            return
        endpoint = parts[1] if len(parts) > 1 else ''
        data = None
        # Support @filename for POST/PUT/PATCH data
        if cmd in ['POST', 'PUT', 'PATCH'] and len(parts) > 2:
            data_arg = parts[2]
            data = self.parse_json(data_arg)
        resp = None
        status = None
        try:
            if cmd == 'GET':
                resp = self.rest_client.get(endpoint)
                status = 200 if resp else None
            elif cmd == 'POST':
                resp = self.rest_client.post(endpoint, data)
                status = 201 if resp else None
            elif cmd == 'PUT':
                resp = self.rest_client.put(endpoint, data)
                status = 200 if resp else None
            elif cmd == 'DELETE':
                resp = self.rest_client.delete(endpoint)
                status = 200 if resp else None
            elif cmd == 'PATCH':
                resp = self.rest_client.patch(endpoint, data)
                status = 200 if resp else None
            self.pretty_print(resp, status, jql_query)
        except Exception as e:
            print(f"Request failed: {e}")

    def handle_pipe_redirect(self, line):
        # Split for redirection
        if '>' in line:
            cmd, filename = line.split('>', 1)
            cmd = cmd.strip()
            filename = filename.strip()
            parts = shlex.split(cmd)
            rest_cmd = parts[0].upper()
            endpoint = parts[1] if len(parts) > 1 else ''
            # Support @filename for POST/PUT/PATCH data
            data = self.parse_json(parts[2]) if len(parts) > 2 else None
            resp = None
            if rest_cmd == 'GET':
                resp = self.rest_client.get(endpoint)
            elif rest_cmd == 'POST':
                resp = self.rest_client.post(endpoint, data)
            elif rest_cmd == 'PUT':
                resp = self.rest_client.put(endpoint, data)
            elif rest_cmd == 'DELETE':
                resp = self.rest_client.delete(endpoint)
            elif rest_cmd == 'PATCH':
                resp = self.rest_client.patch(endpoint, data)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(resp, f, indent=2, ensure_ascii=False)
            print(f"Output written to {filename}")
        elif '|' in line:
            cmd, pipe_cmd = line.split('|', 1)
            cmd = cmd.strip()
            pipe_cmd = pipe_cmd.strip()
            parts = shlex.split(cmd)
            rest_cmd = parts[0].upper()
            endpoint = parts[1] if len(parts) > 1 else ''
            # Support @filename for POST/PUT/PATCH data
            data = self.parse_json(parts[2]) if len(parts) > 2 else None
            resp = None
            if rest_cmd == 'GET':
                resp = self.rest_client.get(endpoint)
            elif rest_cmd == 'POST':
                resp = self.rest_client.post(endpoint, data)
            elif rest_cmd == 'PUT':
                resp = self.rest_client.put(endpoint, data)
            elif rest_cmd == 'DELETE':
                resp = self.rest_client.delete(endpoint)
            elif rest_cmd == 'PATCH':
                resp = self.rest_client.patch(endpoint, data)
            proc = subprocess.Popen(shlex.split(pipe_cmd), stdin=subprocess.PIPE)
            proc.communicate(input=json.dumps(resp, indent=2, ensure_ascii=False).encode('utf-8'))

    def show_help(self):
        print("""
Commands:
  GET /endpoint
  POST /endpoint '{"json": "data"}'
  PUT /endpoint '{"json": "data"}'
  PATCH /endpoint '{"json": "data"}'
  DELETE /endpoint
dry COMMAND               # Show what would be executed
  set var = value           # Set session variable
  alias name = command      # Define alias
  use endpoint_name         # Switch endpoint
  show endpoints            # List configured endpoints
  show vars                 # List session variables
  exit, quit                # Exit shell
  help                      # Show this help
  GET /endpoint > file.json # Redirect output
  GET /endpoint | jq ...    # Pipe output
  GET /endpoint --jql "jmespath_query" # Post-process output with JMESPath
""")

    def show_dry_run(self, line):
        parts = shlex.split(line)
        if not parts:
            print("No command to dry run.")
            return
        cmd = parts[0].upper()
        if cmd not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            print(f"Unknown command: {cmd}")
            return
        endpoint = parts[1] if len(parts) > 1 else ''
        data = None
        if cmd in ['POST', 'PUT', 'PATCH'] and len(parts) > 2:
            data = self.parse_json(parts[2])
        url = f"{self.rest_client.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        print("=== DRY RUN ===")
        print(f"Method: {cmd}")
        print(f"URL: {url}")
        print(f"Headers: {self.rest_client.config.headers}")
        print(f"Timeout: {self.rest_client.config.timeout}")
        if data is not None:
            print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print("================")

if __name__ == '__main__':
    cli = RESTCLI()
    cli.run()