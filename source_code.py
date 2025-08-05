import requests
import json
import sys
import os

class SourceCode:
    def __init__(self):
        self.vars = {}
        self.response = None
        self.headers = {'Content-Type': 'application/json'}  # Default headers

    def execute(self, code):
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            self._execute_line(line)

    def _execute_line(self, line):
        tokens = line.split()
        if not tokens:
            return
            
        command = tokens[0]
        if command == "var":
            self._handle_var(tokens)
        elif command == "api_call":
            self._handle_api_call(tokens)
        elif command == "print":
            self._handle_print(tokens)
        elif command == "set_header":
            self._handle_set_header(tokens)
        else:
            print(f"Unknown command: {command}")

    def _handle_var(self, tokens):
        if len(tokens) < 4 or tokens[2] != '=':
            raise SyntaxError(f"Invalid variable declaration: {' '.join(tokens)}")
            
        var_name = tokens[1]
        value_str = " ".join(tokens[3:])
        
        # Handle different value types
        if value_str.startswith('"') and value_str.endswith('"'):
            value = value_str[1:-1]
        elif value_str.startswith('{') and value_str.endswith('}'):
            try:
                value = json.loads(value_str)
            except json.JSONDecodeError:
                value = value_str
        elif value_str.isdigit():
            value = int(value_str)
        elif value_str.lower() == "true":
            value = True
        elif value_str.lower() == "false":
            value = False
        elif value_str in self.vars:
            value = self.vars[value_str]
        else:
            value = value_str
            
        self.vars[var_name] = value

    def _handle_api_call(self, tokens):
        if len(tokens) < 3:
            raise SyntaxError("API call requires method and URL")
            
        method = tokens[1].upper()
        url = tokens[2]
        
        # Resolve variables in URL
        url = self._resolve_vars(url)
        
        # Prepare request parameters
        params = {}
        data = None
        json_data = None
        
        if method == "GET":
            # Handle query parameters
            if "params" in self.vars:
                params = self.vars["params"]
        else:
            # Handle request body
            if "body" in self.vars:
                if self.headers.get('Content-Type') == 'application/json':
                    json_data = self.vars["body"]
                else:
                    data = self.vars["body"]
        
        # Make the request
        try:
            resp = requests.request(
                method,
                url,
                params=params,
                data=data,
                json=json_data,
                headers=self.headers
            )
            
            # Store response
            self.response = {
                "status": resp.status_code,
                "headers": dict(resp.headers),
                "data": resp.json() if resp.content else None
            }
        except Exception as e:
            print(f"API request failed: {str(e)}")
            self.response = None

    def _handle_set_header(self, tokens):
        if len(tokens) < 3:
            raise SyntaxError("Header requires key and value")
            
        key = tokens[1]
        value = " ".join(tokens[2:])
        self.headers[key] = self._resolve_vars(value)

    def _handle_print(self, tokens):
        if len(tokens) < 2:
            return
            
        target = " ".join(tokens[1:])
        output = self._resolve_vars(target)
        
        # Handle response properties
        if self.response:
            if target == "response.status":
                output = self.response["status"]
            elif target == "response.data":
                output = json.dumps(self.response["data"], indent=2)
            elif target == "response.headers":
                output = json.dumps(self.response["headers"], indent=2)
        
        print(output)

    def _resolve_vars(self, text):
        """Replace ${var} with variable values"""
        if not isinstance(text, str):
            return text
            
        parts = text.split('${')
        if len(parts) == 1:
            return text
            
        result = [parts[0]]
        for part in parts[1:]:
            if '}' not in part:
                result.append(part)
                continue
                
            var_name, remainder = part.split('}', 1)
            value = self.vars.get(var_name, f"${{{var_name}}}")
            result.append(str(value) + remainder)
            
        return ''.join(result)

def run_srcc_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found - {file_path}")
        return
        
    interpreter = SourceCode()
    
    with open(file_path, 'r') as file:
        code = file.read()
        
    try:
        interpreter.execute(code)
    except Exception as e:
        print(f"Runtime error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python source_code.py <filename.srcc>")
        print("Example: python source_code.py example.srcc")
        sys.exit(1)
        
    file_path = sys.argv[1]
    if not file_path.endswith('.srcc'):
        print("Warning: Expected .srcc file extension")
        
    run_srcc_file(file_path)