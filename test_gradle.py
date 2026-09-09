import subprocess
import os

env = os.environ.copy()
env["JAVA_HOME"] = "/usr/lib/jvm/java-17-openjdk-amd64"

try:
    print("Running gradle projects...")
    res = subprocess.run(["gradle", "projects"], cwd="workspace", capture_output=True, text=True, env=env)
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
    
    print("\nRunning gradle tasks...")
    res = subprocess.run(["gradle", "tasks"], cwd="workspace", capture_output=True, text=True, env=env)
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
except Exception as e:
    print("Error:", e)
