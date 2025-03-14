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
                    
def _update_all_pom_properties(project_path, config):
    for root, _, files in os.walk(project_path):
        for file in files:
            if file == "pom.xml":
                file_path = os.path.join(root, file)
                _update_pom_property(file_path, config)

def _update_pom_property(file_path, config):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Define the XML namespace
    ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
    ET.register_namespace('', ns['maven'])
    
    # Locate the <properties> section
    modified = False
    properties = root.find(".//maven:properties", ns)
    if properties is not None:
        for configProjects in config["projects"]:
            for configProperties in configProjects["properties"]:        
                property_element = properties.find(f"maven:{configProperties['property_name']}", ns)
                if property_element is not None:
                    property_element.text = configProperties['property_value']
                    print(f"Updated {configProperties['property_name']} to {configProperties['property_value']}")
                    modified = True                
                else:
                    print(f"Property {configProperties['property_name']} not found in pom.xml.")
    else:
        print("No <properties> section found in pom.xml.")
    if modified:
        tree.write(file_path, xml_declaration=True, encoding='utf-8')
        
def _update_maven_versions(project_path, dependencies, version, parent_version):
    """
    Updates the version of specified dependencies in all pom.xml files within the given Maven project.
    
    :param project_path: Path to the Maven project directory.
    :param dependencies: List of dependency artifactIds to update.
    :param new_version: The new version to set for these dependencies.
    """
    for root, _, files in os.walk(project_path):
        if 'pom.xml' in files:
            pom_path = os.path.join(root, 'pom.xml')
            #print(f"pom_path {pom_path}")
            tree = ET.parse(pom_path)
            root_element = tree.getroot()
            
            # Define the XML namespaces
            namespaces = {'m': 'http://maven.apache.org/POM/4.0.0'}
            ET.register_namespace('', namespaces['m'])
            
            modified = False

            # Update the version of the project itself
            for project_version in root_element.findall("./m:version", namespaces):
                if project_version is not None:
                    project_version.text = version
                    modified = True

            # Update the parent version
            for parent_tag in root_element.findall("./m:parent", namespaces):
                if parent_tag is not None:
                    for parent_vers in parent_tag.findall("./m:version", namespaces):                      
                        if parent_vers is not None:    
                            parent_vers.text = parent_version
                            modified = True
            
            
            for dependency in root_element.findall(".//m:dependency", namespaces):
                artifact_id_elem = dependency.find("m:artifactId", namespaces)
                version_elem = dependency.find("m:version", namespaces)
                
                if artifact_id_elem is not None and version_elem is not None:
                    for dependency in dependencies:
                        if artifact_id_elem.text in dependency["dependency_name"]:
                            print(f"artifact_id_elem.text {artifact_id_elem.text}")
                            version_elem.text = dependency["dependency_version"]
                            modified = True
                            #print(f"Updated {artifact_id_elem.text} in {pom_path} to version {version}")
            
            if modified:
                tree.write(pom_path, xml_declaration=True, encoding='utf-8')
                #print(f"Updated dependencies in {pom_path}")

# Example usage
# update_maven_dependencies('/path/to/maven/project', ['dependency1', 'dependency2'], '1.2.3')


def _update_maven_versions_from_yaml(project):    
    project_path = project.get("project_path")
    parent_version = project.get("parent_version")
    dependencies = project.get("dependencies", [])
    version = project.get("version")
    if not project_path or not dependencies or not version:
        raise ValueError("YAML file must contain 'project_path', 'dependencies', and 'version' fields.")
    
    _update_maven_versions(project_path, dependencies, version, parent_version)

                                       
                    
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
        _git_checkout_and_pull(project["project_path"])
        if project["type"] == "Maven":
            _update_all_pom_properties(project["project_path"], config)
            _update_maven_versions_from_yaml(project)
        elif project["type"] == "Ant":
            _update_ant_version(project["project_path"], project["version"], project["version_file"])
        elif project["type"] == "Angular":
            _update_angular_version(project["project_path"], project["version"], project["version_file"])

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
