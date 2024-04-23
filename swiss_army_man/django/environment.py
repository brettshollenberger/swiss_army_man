import os
import re
import sys
import yaml
from .. import project_root

def erb_substitute(match):
    env_var = match.group(1)
    return os.environ.get(env_var, '')

def load_erb_yaml(file):
    content = file.read()

    # Replace ERB syntax with environment variable values
    content = re.sub(r'<%= ENV\[\'(.*?)\'\] %>', erb_substitute, content)

    return yaml.safe_load(content)


def db_config():
    if 'pytest' in sys.modules:
        django_env = 'test'
    else:
        django_env = os.getenv('DJANGO_ENV', 'development')

    with open(os.path.join(project_root('db/config.yml')), 'r') as f:
        db_config = load_erb_yaml(f)

    # Get the configuration for the current environment
    return db_config[django_env]