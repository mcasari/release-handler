import yaml
import os
import subprocess
import logging
import click

# Configure logging
logging.basicConfig(filename='release-handler.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def _execute_command(command, cwd):
    """Executes a shell command in a given directory."""
    try:
        subprocess.run(command, cwd=cwd, check=True, shell=True)
        logging.info(f"Executed: {' '.join(command)} in {cwd}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")

def _update_maven_version(path, version):
    """Updates the Maven project version."""
    _execute_command(["mvn", "versions:set", f"-DnewVersion={version}", "-DgenerateBackupPoms=false"], path)
    _execute_command(["mvn", "versions:commit"], path)

def _update_ant_version(path, version, version_file):
    """Updates the Ant project version."""
    version_file_path = os.path.join(path, version_file)
    with open(version_file_path, 'r') as file:
        content = file.read()
    content = content.replace("version=", f"version={version}")
    with open(version_file_path, 'w') as file:
        file.write(content)
    logging.info(f"Updated Ant version in {version_file_path} to {version}")

def _update_angular_version(path, version, version_file):
    """Updates the Angular project version."""
    version_file_path = os.path.join(path, version_file)
    with open(version_file_path, 'r') as file:
        content = file.read()
    content = content.replace("\"version\": \"", f"\"version\": \"{version}\"")
    with open(version_file_path, 'w') as file:
        file.write(content)
    logging.info(f"Updated Angular version in {version_file_path} to {version}")

def _git_checkout_and_pull(path):
    """Performs git checkout on master and pulls latest changes."""
    _execute_command(["git", "checkout", "master"], path)
    _execute_command(["git", "pull"], path)

def process_projects():
    """Reads the YAML file and processes each project."""
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    for project in config["projects"]:
        _git_checkout_and_pull(project["folder"])
        if project["type"] == "Maven":
            _update_maven_version(project["folder"], project["version"])
        elif project["type"] == "Ant":
            _update_ant_version(project["folder"], project["version"], project["version_file"])
        elif project["type"] == "Angular":
            _update_angular_version(project["folder"], project["version"], project["version_file"])

def tag_projects():
    """Tags each project with the appropriate tag name."""
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    for project in config["projects"]:
        tag = f"{config['environment']}-{project['tag']}"
        _execute_command(["git", "tag", tag], project["folder"])
        logging.info(f"Tagged {project['name']} with {tag}")

def commit_projects():
    """Commits changes for each project with confirmation."""
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    for project in config["projects"]:
        if click.confirm(f"Commit changes for {project['name']}?"):
            _execute_command(["git", "commit", "-am", f"Updated version for {project['name']}"] , project["folder"])

def push_projects():
    """Pushes commits for each project with confirmation."""
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    for project in config["projects"]:
        if click.confirm(f"Push changes for {project['name']}?"):
            _execute_command(["git", "push"], project["folder"])

def reset_lastcommit():
    """Resets the last commit based on reset-type."""
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    for project in config["projects"]:
        if click.confirm(f"Reset last commit for {project['name']}?"):
            _execute_command(["git", "reset", f"--{config['reset-type']}"] , project["folder"])

@click.group()
def cli():
    pass

cli.add_command(process_projects)
cli.add_command(tag_projects)
cli.add_command(commit_projects)
cli.add_command(push_projects)
cli.add_command(reset_lastcommit)

if __name__ == "__main__":
    cli()
