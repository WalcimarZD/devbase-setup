## 2024-05-22 - Command Injection in PKM Commands
**Vulnerability:** The `devbase pkm journal` and `devbase pkm icebox` commands were using `subprocess.run(f'code "{file_path}"', shell=True)` to open files in VS Code. This is vulnerable to command injection if `file_path` contains malicious shell characters (e.g., `"; rm -rf /"`).
**Learning:** Even internal CLI tools can be vulnerable if they construct shell commands from variables. `shell=True` should almost always be avoided in Python.
**Prevention:** Always use `subprocess.run` with a list of arguments (e.g., `['code', str(file_path)]`) and `shell=False` (the default). This forces the arguments to be passed directly to the executable without shell interpretation.
