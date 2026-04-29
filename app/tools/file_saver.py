import os
import re


def save_files(code_output: str, base_path: str = "workspace"):
    """Parse LLM output with FILE: markers and save each file.

    Expected format:
        FILE: path/to/file.kt
        <file content>

        FILE: path/to/another.xml
        <file content>
    """
    os.makedirs(base_path, exist_ok=True)

    files = code_output.split("FILE:")

    saved_files = []

    for file in files:
        if not file.strip():
            continue

        lines = file.strip().split("\n")
        file_path = lines[0].strip()

        # Validate: skip if this doesn't look like a real file path
        if not _is_valid_path(file_path):
            # --- DEBUG (uncomment for debugging) ---
            # print(f"├─ [FILE_SAVER] DEBUG skipping invalid path: {file_path[:80]}...")
            continue

        content = "\n".join(lines[1:])

        full_path = os.path.join(base_path, file_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w") as f:
            f.write(content)

        saved_files.append(full_path)

    # --- DEBUG (uncomment for debugging) ---
    # print(f"├─ [FILE_SAVER] DEBUG saved {len(saved_files)} files: {saved_files}")

    return saved_files


def _is_valid_path(path: str) -> bool:
    """Check if a string looks like a valid file path vs. prose text."""
    # Too long for a file path
    if len(path) > 200:
        return False
    # Must contain a dot (file extension) somewhere
    if "." not in path:
        return False
    # Should not contain multiple spaces (prose indicator)
    if "  " in path or path.count(" ") > 3:
        return False
    # Should match a path-like pattern (letters, numbers, slashes, dots, dashes, underscores)
    if not re.match(r'^[\w\s./\\-]+$', path):
        return False
    return True