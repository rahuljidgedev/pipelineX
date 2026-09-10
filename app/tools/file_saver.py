from app.core.constants import WORKSPACE_DIR
import os
import re
import shutil

def _enforce_kmp_imports(content: str, file_path: str) -> str:
    if not file_path.endswith(".kt"):
        return content
    if "@Composable" not in content and "androidx.compose" not in content:
        return content
    mandatory_imports = (
        "import androidx.compose.foundation.*\n"
        "import androidx.compose.foundation.layout.*\n"
        "import androidx.compose.ui.*\n"
        "import androidx.compose.material3.*\n"
        "import androidx.compose.runtime.*\n"
        "import androidx.compose.ui.unit.*\n"
        "import androidx.compose.ui.graphics.*\n"
        "import androidx.compose.ui.text.*\n"
        "import androidx.compose.ui.text.style.*\n"
        "import androidx.compose.ui.text.font.*\n"
        "import androidx.compose.material.icons.Icons\n"
        "import androidx.compose.material.icons.filled.*\n"
    )
    
    # Strip existing compose imports to prevent "Conflicting import" errors
    content = re.sub(r'^import androidx\.compose\..*?\n', '', content, flags=re.MULTILINE)
    
    package_match = re.search(r'^package [^\n]+', content, re.MULTILINE)
    if package_match:
        insert_pos = package_match.end()
        return content[:insert_pos] + "\n\n// AUTO-INJECTED KMP IMPORTS\n" + mandatory_imports + content[insert_pos:]
    return content


def clear_workspace(base_path: str = WORKSPACE_DIR):
    """Remove all files and directories in the workspace."""
    if os.path.exists(base_path):
        for filename in os.listdir(base_path):
            file_path = os.path.join(base_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        os.makedirs(base_path, exist_ok=True)


LOCKED_FILES = [
    "build.gradle.kts",
    "settings.gradle.kts",
    "gradle.properties",
    "gradlew",
    "gradlew.bat",
    "androidmain/androidmanifest.xml"
]

def _is_locked_file(path: str) -> bool:
    normalized = path.lower().replace("\\", "/")
    return any(norm_locked in normalized for norm_locked in LOCKED_FILES)


def apply_patch(file_path: str, search_content: str, replace_content: str) -> bool:
    """Read file, search for search_content, replace it with replace_content, and write back."""
    if not os.path.exists(file_path):
        print(f"├─ [FILE_SAVER] ❌ Patch failed: File does not exist: {file_path}")
        return False
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Standardize newlines for robust matching
        content_std = content.replace("\r\n", "\n")
        search_std = search_content.replace("\r\n", "\n")
        replace_std = replace_content.replace("\r\n", "\n")
        
        if search_std not in content_std:
            # Fallback to loose matching (stripping trailing/leading whitespaces per line)
            print(f"├─ [FILE_SAVER] ⚠️ Exact patch match failed. Attempting line-normalized match...")
            search_lines = [l.strip() for l in search_std.strip().split("\n") if l.strip()]
            content_lines = content_std.split("\n")
            
            # Find matching sub-segment
            matched = False
            for i in range(len(content_lines) - len(search_lines) + 1):
                sub_segment = [content_lines[j].strip() for j in range(i, i + len(search_lines))]
                if sub_segment == search_lines:
                    # Found! Let's reconstruct content
                    content_std = "\n".join(content_lines[:i]) + "\n" + replace_std + "\n" + "\n".join(content_lines[i + len(search_lines):])
                    matched = True
                    break
            
            if not matched:
                print(f"├─ [FILE_SAVER] ❌ Patch failed: Search block not found in {file_path}")
                return False
        else:
            content_std = content_std.replace(search_std, replace_std, 1)
            
        content_std = _enforce_kmp_imports(content_std, file_path)
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_std)
            
        print(f"├─ [FILE_SAVER] 🩹 Patch applied successfully to: {file_path}")
        return True
    except Exception as e:
        print(f"├─ [FILE_SAVER] ❌ Failed to apply patch: {e}")
        return False


def save_files(code_output: str, base_path: str = WORKSPACE_DIR):
    """Parse LLM output with FILE: markers and save or patch each file."""
    # Ensure workspace exists
    os.makedirs(base_path, exist_ok=True)
    
    print(f"├─ [FILE_SAVER] 🔍 Analyzing {len(code_output)} chars of output...")

    # Primary method: Split by FILE: marker
    # We use a regex that matches "FILE:" at the start of a line or after a newline
    file_blocks = re.split(r'(?m)^FILE:\s*', code_output)
    saved_files = []

    for block in file_blocks:
        if not block.strip():
            continue
        
        lines = block.split("\n")
        raw_path = lines[0].strip().strip("*`[] \"':")
        
        if _is_valid_path(raw_path):
            if _is_locked_file(raw_path):
                print(f"├─ [FILE_SAVER] 🔒 Blocked write to locked file: {raw_path}")
                continue

            block_body = "\n".join(lines[1:]).strip()
            
            # Check if this block is a PATCH block
            if "<<<< SEARCH" in block_body:
                # Parse search-replace blocks
                # Look for <<<< SEARCH\n(.*?)\n==== REPLACE\n(.*?)\n>>>> END
                patch_pattern = re.compile(r'<<<< SEARCH\n(.*?)\n==== REPLACE\n(.*?)\n>>>> END', re.DOTALL)
                patches = patch_pattern.findall(block_body)
                
                if patches:
                    full_path = os.path.join(base_path, raw_path)
                    success_all = True
                    for search_str, replace_str in patches:
                        ok = apply_patch(full_path, search_str, replace_str)
                        if not ok:
                            success_all = False
                    if success_all:
                        saved_files.append(raw_path)
                    continue

            # Standard complete file generation/overwrite
            content = block_body
            match = re.search(r'```(?:\w+)?\n?(.*?)\n?```', content, re.DOTALL)
            if match:
                content = match.group(1).strip()
                
            content = _enforce_kmp_imports(content, raw_path)
            
            full_path = os.path.join(base_path, raw_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f: 
                f.write(content)
            saved_files.append(raw_path)

    # Fallback method: If primary split didn't yield valid files, try a global regex find
    if not saved_files:
        print("├─ [FILE_SAVER] ⚠️  Primary parse failed. Attempting deep scan...")
        # Regex to find FILE: markers and their following content until the next FILE: or end
        pattern = re.compile(r'(?i)FILE:\s*([^\n]+)\n(.*?)(?=FILE:|$)', re.DOTALL)
        matches = pattern.findall(code_output)
        
        for raw_path, content in matches:
            raw_path = raw_path.strip().strip("*`[] \"':")
            if _is_valid_path(raw_path):
                if _is_locked_file(raw_path):
                    print(f"├─ [FILE_SAVER] 🔒 Blocked write to locked file: {raw_path}")
                    continue

                content_str = content.strip()
                if "<<<< SEARCH" in content_str:
                    # Fallback patch
                    patch_pattern = re.compile(r'<<<< SEARCH\n(.*?)\n==== REPLACE\n(.*?)\n>>>> END', re.DOTALL)
                    patches = patch_pattern.findall(content_str)
                    if patches:
                        full_path = os.path.join(base_path, raw_path)
                        success_all = True
                        for search_str, replace_str in patches:
                            ok = apply_patch(full_path, search_str, replace_str)
                            if not ok:
                                success_all = False
                        if success_all:
                            saved_files.append(raw_path)
                        continue

                # Clean content (strip code blocks)
                match = re.search(r'```(?:\w+)?\n?(.*?)\n?```', content, re.DOTALL)
                if match:
                    content_str = match.group(1).strip()
                
                full_path = os.path.join(base_path, raw_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                # Fallback for full file block in regex
                content_str = _enforce_kmp_imports(content_str, raw_path)
                with open(full_path, "w") as f:
                    f.write(content_str)
                saved_files.append(raw_path)

    print(f"├─ [FILE_SAVER] ✅ Saved {len(saved_files)} files: {saved_files}")
    return saved_files


def _is_valid_path(path: str) -> bool:
    """Check if a string looks like a valid file path."""
    if not path or len(path) > 250:
        return False
    # Should look like a path (slashes, dots, alphanumeric)
    if not re.search(r'^[\w/\\.-]+$', path):
        return False
    return True