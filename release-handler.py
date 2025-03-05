import yaml
import subprocess
import logging
import os
from tkinter import messagebox

# Configure logging
logging.basicConfig(filename='release-handler.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_projects(yaml_file):
    with open(yaml_file, 'r') as file:
        return yaml.safe_load(file)['projects']

def run_command(command, cwd):
    result = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        logging.info(f"Command succeeded: {command}")
    else:
        logging.error(f"Command failed: {command}\n{result.stderr}")

def checkout_and_pull(project_path):
    logging.info(f"Checking out master and pulling for {project_path}")
    run_command("git checkout master", project_path)
    run_command("git pull", project_path)

def change_maven_version(project_path, new_version):
    logging.info(f"Changing Maven project version in {project_path} to {new_version}")
    run_command(f"mvn versions:set -DnewVersion={new_version} -DgenerateBackupPoms=false", project_path)
    run_command("mvn versions:commit", project_path)

def change_ant_version(project_path, version_property, new_version, version_file):
    logging.info(f"Updating Ant project version in {project_path}")
    version_file_path = os.path.join(project_path, version_file)
    with open(version_file_path, 'r') as file:
        content = file.read()
    new_content = content.replace(f'{version_property}=old_version', f'{version_property}={new_version}')
    with open(version_file_path, 'w') as file:
        file.write(new_content)

def change_angular_version(project_path, new_version, version_file):
    logging.info(f"Updating Angular project version in {project_path}")
    version_file_path = os.path.join(project_path, version_file)
    with open(version_file_path, 'r') as file:
        content = file.read()
    new_content = content.replace('"version": "old_version"', f'"version": "{new_version}"')
    with open(version_file_path, 'w') as file:
        file.write(new_content)

def process_projects(yaml_file):
    projects = load_projects(yaml_file)
    for project in projects:
        checkout_and_pull(project['path'])
        if project['type'] == 'Maven':
            change_maven_version(project['path'], project['version'])
        elif project['type'] == 'Ant':
            change_ant_version(project['path'], project['version_name'], project['version'], project['version_file'])
        elif project['type'] == 'Angular':
            change_angular_version(project['path'], project['version'], project['version_file'])

def tag_projects(yaml_file):
    projects = load_projects(yaml_file)
    for project in projects:
        logging.info(f"Tagging project {project['path']} with {project['tag']}")
        run_command(f"git tag {project['tag']}", project['path'])

def commit_projects(yaml_file):
    projects = load_projects(yaml_file)
    for project in projects:
        if messagebox.askyesno("Confirm Commit", f"Commit changes for {project['path']}?"):
            logging.info(f"Committing project {project['path']}")
            run_command("git add .", project['path'])
            run_command("git commit -m 'Version update'", project['path'])

def push_projects(yaml_file):
    projects = load_projects(yaml_file)
    for project in projects:
        if messagebox.askyesno("Confirm Push", f"Push changes for {project['path']}?"):
            logging.info(f"Pushing project {project['path']}")
            run_command("git push", project['path'])

def reset_lastcommit(yaml_file):
    projects = load_projects(yaml_file)
    for project in projects:
        reset_type = project['reset-type'].lower()
        if messagebox.askyesno("Confirm Reset", f"Reset last commit ({reset_type}) for {project['path']}?"):
            logging.info(f"Resetting last commit ({reset_type}) for {project['path']}")
            run_command(f"git reset --{reset_type}", project['path'])