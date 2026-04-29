import os

def save_project(code_output: str, base_path: str):
    current_file = None
    content = []

    for line in code_output.splitlines():
        if line.startswith("FILE:"):
            if current_file:
                write_file(base_path, current_file, "\n".join(content))
            current_file = line.replace("FILE:", "").strip()
            content = []
        else:
            content.append(line)

    if current_file:
        write_file(base_path, current_file, "\n".join(content))


def write_file(base, path, content):
    full_path = os.path.join(base, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w") as f:
        f.write(content)