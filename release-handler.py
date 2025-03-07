import yaml
import os
import subprocess
import logging
import sys
import xml.etree.ElementTree as ET
import re

# Configure logging
logging.basicConfig(filename='release-handler.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
                    
def _update_maven_version(project_path, new_version):
    """
    Updates the versions in a multi-module Maven project.
    :param project_path: Path to the root of the Maven project.
    :param new_version: The new version to set in pom.xml files.
    """
    if not os.path.isdir(project_path):
        raise ValueError("Invalid project path")
    
    # Collect all pom.xml files
    pom_files = []
    for root, _, files in os.walk(project_path):
        if 'pom.xml' in files:
            pom_files.append(os.path.join(root, 'pom.xml'))
    
    for pom_file in pom_files:
        with open(pom_file, 'r', encoding='utf-8') as file:
            content = file.read()
            content = re.sub(r'xmlns(\w+)?="[^"]+"', '', content)
            print(content)
        root = ET.fromstring(content)
        
        # Update project version
        for elem in root.findall("./version"):
            elem.text = new_version
        
        # Update parent version if present
        for elem in root.findall("./parent/version"):
            elem.text = new_version
        
        # Update dependency versions
        for dependency in root.findall(".//dependency"):
            version = dependency.find("version")
            if version is not None:
                version.text = new_version
        
        # Save changes without adding namespaces
        tree = ET.ElementTree(root)
        tree.write(pom_file, encoding="utf-8", xml_declaration=True)
    
    logging.info(f"Updated all module versions to {new_version}")                   
                    
def _find_file(base_path, filename):
    for root, _, files in os.walk(base_path):
        if filename in files:
            return os.path.join(root, filename)  
    return None
    
def _execute_command(command, cwd):
    """Executes a shell command in a given directory."""
    try:
        subprocess.run(command, cwd=cwd, check=True, shell=True)
        logging.info(f"Executed: {' '.join(command)} in {cwd}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")

def _update_ant_version(path, version, version_file):
    """Updates the Ant project version."""
    version_file_path = _find_file(path, version_file)
    with open(version_file_path, 'r') as file:
        content = file.read()
    content = content.replace("version=", f"version={version}")
    with open(version_file_path, 'w') as file:
        file.write(content)
    logging.info(f"Updated Ant version in {version_file_path} to {version}")

def _update_angular_version(path, version, version_file):
    """Updates the Angular project version."""
    version_file_path = _find_file(path, version_file)
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

def update_versions():
    """Reads the YAML file and processes each project."""
    with open("release-handler-config.yaml", "r") as file:
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
    with open("release-handler-config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    for project in config["projects"]:
        tag = f"{config['environment']}-{project['tag']}"
        _execute_command(["git", "tag", tag], project["folder"])
        logging.info(f"Tagged {project['name']} with {tag}")

def commit_projects():
    """Commits changes for each project with confirmation."""
    with open("release-handler-config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    for project in config["projects"]:
        if click.confirm(f"Commit changes for {project['name']}?"):
            _execute_command(["git", "commit", "-am", f"Updated version for {project['name']}"] , project["folder"])

def push_projects():
    """Pushes commits for each project with confirmation."""
    with open("release-handler-config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    for project in config["projects"]:
        if click.confirm(f"Push changes for {project['name']}?"):
            _execute_command(["git", "push"], project["folder"])

def reset_lastcommit():
    """Resets the last commit based on reset-type."""
    with open("release-handler-config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    for project in config["projects"]:
        if click.confirm(f"Reset last commit for {project['name']}?"):
            _execute_command(["git", "reset", f"--{config['reset-type']}"] , project["folder"])



if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "update_versions":
            update_versions()
            
    else:
        print("Usage: python script.py <name>")
