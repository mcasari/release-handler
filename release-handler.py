import yaml
import subprocess
import logging
import os

# Configure logging
logging.basicConfig(filename='release-handler.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def change_maven_version(path, version):
    """Changes Maven project version."""
    try:
        subprocess.run(["mvn", "versions:set", f"-DnewVersion={version}", "-DgenerateBackupPoms=false"], cwd=path, check=True)
        logging.info(f"Maven project at {path} updated to version {version}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update Maven project at {path}: {e}")

def change_ant_version(path, version_name, version_value, version_file):
    """Changes Ant project version in the specified version file."""
    version_path = os.path.join(path, version_file)
    try:
        with open(version_path, 'r') as file:
            content = file.read()
        content = content.replace(f'{version_name}=.*', f'{version_name}={version_value}')
        with open(version_path, 'w') as file:
            file.write(content)
        logging.info(f"Ant project at {path} updated to version {version_value} in {version_file}.")
    except Exception as e:
        logging.error(f"Failed to update Ant project at {path}: {e}")

def change_angular_version(path, version_value, version_file):
    """Changes Angular project version in package.json."""
    version_path = os.path.join(path, version_file)
    try:
        with open(version_path, 'r') as file:
            content = file.read()
        content = content.replace('"version": ".*"', f'"version": "{version_value}"')
        with open(version_path, 'w') as file:
            file.write(content)
        logging.info(f"Angular project at {path} updated to version {version_value} in {version_file}.")
    except Exception as e:
        logging.error(f"Failed to update Angular project at {path}: {e}")

def update_versions_from_yaml(yaml_file):
    """Reads YAML file and updates project versions accordingly."""
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    
    for project in data['projects']:
        path = project['path']
        project_type = project['type']
        version = project['version']['value']
        version_file = project['version']['file']
        
        if project_type == 'Maven':
            change_maven_version(path, version)
        elif project_type == 'Ant':
            change_ant_version(path, project['version']['name'], version, version_file)
        elif project_type == 'Angular':
            change_angular_version(path, version, version_file)

def tag_projects(yaml_file):
    """Tags projects as per YAML file."""
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    
    for project in data['projects']:
        path = project['path']
        tag = project['tag']
        try:
            subprocess.run(["git", "tag", tag], cwd=path, check=True)
            logging.info(f"Tagged project at {path} with {tag}.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to tag project at {path}: {e}")

def commit_projects(yaml_file):
    """Commits changes for all projects in the YAML file."""
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    
    for project in data['projects']:
        path = project['path']
        try:
            subprocess.run(["git", "add", "-A"], cwd=path, check=True)
            subprocess.run(["git", "commit", "-m", "Updated project version"], cwd=path, check=True)
            logging.info(f"Committed changes for project at {path}.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to commit project at {path}: {e}")

def push_projects(yaml_file):
    """Pushes commits for all projects after confirmation."""
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    
    for project in data['projects']:
        path = project['path']
        confirm = input(f"Push changes for {path}? (yes/no): ")
        if confirm.lower() == 'yes':
            try:
                subprocess.run(["git", "push"], cwd=path, check=True)
                logging.info(f"Pushed changes for project at {path}.")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to push project at {path}: {e}")
