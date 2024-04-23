import subprocess
import os

def _project_root():
    # First strategy: Use git command
    try:
        root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'])
        return root.decode('utf-8').strip()
    except Exception as e:
        pass  # If this fails, we proceed to the next strategy

    # Second strategy: Use the script's directory and adjust for expected structure
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Assuming this script is two directories down from the root.
        root_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
        return root_dir
    except Exception as e:
        pass  # If this fails, we proceed to the next strategy

    # (Optional) Third strategy: Use current working directory
    try:
        return os.getcwd()
    except Exception as e:
        pass  # If this fails, we can't determine the root

    raise EnvironmentError("Unable to determine the project root")

def project_root(path=""):
    return os.path.join(_project_root(), path)