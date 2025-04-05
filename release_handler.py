import yaml
import os
import subprocess
import logging
import sys
import xml.etree.ElementTree as ET
import re
import click
import platform

# Configure logging
logging.basicConfig(filename='release-handler.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
                    
def _is_tag_committed(tag_name, repo_path):
    """
    Check if a given Git tag exists in the repository.

    Args:
        tag_name (str): The name of the tag to check.
        repo_path (str): Path to the Git repository (default is current directory).

    Returns:
        bool: True if the tag exists (i.e., is committed), False otherwise.
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--verify', f'refs/tags/{tag_name}'],
            cwd=repo_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking tag: {e}")
        return False        
 
def _list_git_changes(project_path):
    """
    Lists all tracked changes (modified, added, deleted) in a Git repository.
    
    :param project_path: Path to the Git project.
    :return: A dictionary containing lists of modified, added, and deleted files.
    """
    if not os.path.isdir(project_path):
        raise ValueError("Invalid project path")
    
    git_command = ["git", "status", "--porcelain"]
    try:
        result = subprocess.run(git_command, cwd=project_path, capture_output=True, text=True, check=True)
        changes = result.stdout.strip().split('\n')
        
        modified = []
        added = []
        deleted = []
        
        for change in changes:
            if change:
                status, file = change[:2].strip(), change[3:].strip()
                if status in ('M', 'MM'):
                    modified.append(file)
                elif status in ('A', 'AM'):
                    added.append(file)
                elif status in ('D', 'DM'):
                    deleted.append(file)
        
        return {"modified": modified, "added": added, "deleted": deleted}
    
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error executing git command: {e}")
        
def _is_tag_pushed(project_path, tag_name) -> bool:
    """
    Checks if a given tag is already pushed to the remote repository.
    
    :param project_path: Path to the local git repository.
    :param tag_name: Name of the tag to check.
    :return: True if the tag is pushed, False otherwise.
    """
    try:
        # Get the list of tags from the remote
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "origin"],
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # Check if the tag exists in the remote
        return any(f"refs/tags/{tag_name}" in line for line in result.stdout.splitlines())
    except subprocess.CalledProcessError as e:
        print(f"Error checking remote tags: {e.stderr}")
        return False
        
def _compile_maven_project(project_path, maven_home, settings_file, config) -> bool:
    """
    Compiles a Maven project while skipping tests.
    
    :param project_path: Path to the Maven project.
    :param maven_home: Path to the Maven home directory.
    :param settings_file: Path to the Maven settings file.
    :return: True if compilation succeeds, False otherwise.
    """
    is_windows = platform.system() == "Windows"
    mvn_executable = os.path.join(maven_home, "bin", "mvn.cmd" if is_windows else "mvn")
    command = [mvn_executable, "clean", "compile", "--settings", settings_file]
    maven_compile_options = config.get("maven_compile_options", [])
    install_index = command.index("compile")
    command = command[:install_index + 1] + maven_compile_options + command[install_index + 1:]
    
    try:
        result = subprocess.run(command, cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return True
        else:
            logging.info("Maven build failed:", result.stderr)
            print("Maven build failed:", result.stderr)
            return False
    except Exception as e:
        logging.error(f"Error running Maven: {e}")
        print(f"Error running Maven: {e}")
        return False
        
def _compile_angular_project(project_path, config) -> bool:
    """
    Checks if an Angular project compiles correctly.
    :param project_path: Path to the Angular project.
    :return: True if the project compiles successfully, False otherwise.
    """
    if not os.path.isdir(project_path):
        logging.error("Invalid project path.")
        print("Invalid project path.")
        return False
    
    try:
        # Run the Angular build command
        npm_command = os.path.join(config["nodejs_home"], "ng")
        is_windows = platform.system() == "Windows"
        if is_windows:
            npm_command = os.path.join(config["nodejs_home"], "ng.cmd")
        nodejs_compile_options = config.get("nodejs_compile_options", [])
        npm_command_arr = [npm_command, "build"] + nodejs_compile_options;
        result = subprocess.run(
            npm_command_arr, cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode == 0:
            return True
        else:
            logging.info("Build failed:", result.stderr)
            print("Build failed:", result.stderr)
            return False
    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
        print(f"Error: {e}")
        return False

# Example usage:
# print(check_angular_compile("/path/to/angular/project"))

def _compile_ant_project(project_path, config) -> bool:
    """
    Compiles an Ant project.
    
    :param project_path: Path to the Ant project.
    :param ant_home: Path to the Ant home directory.
    :param ant_target: The Ant target to execute.
    :return: True if compilation is successful, False otherwise.
    """
    ant_executable = os.path.join(config["ant_home"], 'bin', 'ant')
    is_windows = platform.system() == "Windows"
    if is_windows:
        ant_executable = os.path.join(config["ant_home"], 'bin', 'ant.bat')
    command = [ant_executable, config["ant_target"]] + config["ant_compile_options"]
    
    try:
        result = subprocess.run(command, cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logging.info(result.stderr)
        print(result.stderr)
        if "failed" in result.stderr:
            raise ValueError("Unexpected error during build: " + result.stderr)       
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Error executing Ant: {e}")
        print(f"Error executing Ant: {e}")
        return False

# Example usage:
# success = compile_ant_project("/path/to/project", "/path/to/ant", "build")
# print("Compilation Successful" if success else "Compilation Failed")

def _is_last_commit_pushed(project_path):
    try:
        # Get the latest commit hash
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project_path
        ).strip().decode("utf-8")

        # Check if the commit is in the remote
        remote_branches = subprocess.check_output(
            ["git", "branch", "-r", "--contains", commit_hash], cwd=project_path
        ).strip().decode("utf-8")

        # If the commit exists in remote branches, it's pushed
        return bool(remote_branches)
    except subprocess.CalledProcessError:
        return False              
                                        
def _resolve_placeholders(data, context=None):
    """ Recursively resolves placeholders in a dictionary using string formatting """
    if context is None:
        context = data  # Initial context is the entire data
    
    if isinstance(data, dict):
        return {key: _resolve_placeholders(value, context) for key, value in data.items()}
    elif isinstance(data, list):
        return [_resolve_placeholders(item, context) for item in data]
    elif isinstance(data, str):
        try:
            return data.format(**context)  # Use Python string formatting
        except KeyError:
            return data  # Return as-is if placeholders are unresolved
    else:
        return data  # Return non-string values unchanged
                    
def _update_all_pom_properties(project, config):
    for root, _, files in os.walk(project["project_path"]):
        for file in files:
            if file == "pom.xml":
                file_path = os.path.join(root, file)
                _update_pom_property(file_path, project, config)

def _update_pom_property(file_path, project, config):
    tree = ET.parse(file_path)
    root = tree.getroot()
    maven_namespace = config["maven_namespace"]
    
    # Define the XML namespace
    ns = {'maven': maven_namespace}
    ET.register_namespace('', ns['maven'])
    
    # Locate the <properties> section
    modified = False
    properties = root.find(".//maven:properties", ns)
    if properties is not None:     
        if project["type"] == "Maven":
            for configProperties in project["properties"]:                 
                property_element = properties.find(f"maven:{configProperties['property_name']}", ns)
                if property_element is not None:
                    property_element.text = configProperties['property_value']
                    logging.info(f"Updated {configProperties['property_name']} to {configProperties['property_value']}")
                    print(f"Updated {configProperties['property_name']} to {configProperties['property_value']}")
                    modified = True                
                else:
                    logging.info(f"Property {configProperties['property_name']} not found in pom.xml.")
                    print(f"Property {configProperties['property_name']} not found in pom.xml.")
    else:
        logging.info("No <properties> section found in pom.xml.")
        print("No <properties> section found in pom.xml.")
    if modified:
        tree.write(file_path, xml_declaration=True, encoding='utf-8')
        
def _update_maven_versions(project_path, dependencies, version, parent_version, maven_namespace):
    for root, _, files in os.walk(project_path):
        if 'pom.xml' in files:
            pom_path = os.path.join(root, 'pom.xml')
            tree = ET.parse(pom_path)
            root_element = tree.getroot()
            
            # Define the XML namespaces
            # Define the XML namespace
            namespaces = {'m': maven_namespace}
            ET.register_namespace('', namespaces['m'])
            
            modified = False

            # Update the version of the project itself
            for project_version in root_element.findall("./m:version", namespaces):
                if project_version is not None:
                    project_version.text = version
                    modified = True
                    logging.info(f"Project version updated to {version}")
                    print(f"Project version updated to {version}")

            # Update the parent version
            for parent_tag in root_element.findall("./m:parent", namespaces):
                if parent_tag is not None:
                    for parent_vers in parent_tag.findall("./m:version", namespaces):                      
                        if parent_vers is not None:
                            parent_vers.text = parent_version
                            modified = True
                            logging.info(f"Parent version updated to {version}")
                            print(f"Parent version updated to {version}")
            
            
            for dependency in root_element.findall(".//m:dependency", namespaces):
                artifact_id_elem = dependency.find("m:artifactId", namespaces)
                version_elem = dependency.find("m:version", namespaces)
                
                if artifact_id_elem is not None and version_elem is not None:
                    for dependency in dependencies:
                        if artifact_id_elem.text in dependency["dependency_name"]:
                            version_elem.text = dependency["dependency_version"]
                            modified = True
                            logging.info(f"Dependency {dependency["dependency_name"]}  updated to {dependency["dependency_version"]}")
                            print(f"Dependency {dependency["dependency_name"]}  updated to {dependency["dependency_version"]}")            
            if modified:
                tree.write(pom_path, xml_declaration=True, encoding='utf-8')

def _update_maven_versions_from_yaml(project, config):    
    maven_namespace = config["maven_namespace"]
    project_path = project.get("project_path")
    parent_version = project.get("parent_version")
    dependencies = project.get("dependencies", [])
    version = project.get("version")
    if not project_path or not dependencies or not version or not maven_namespace:
        raise ValueError("YAML file must contain 'maven_namespace', 'project_path', 'parent_version', 'dependencies' and 'version' fields.")
    
    _update_maven_versions(project_path, dependencies, version, parent_version, maven_namespace)

                                       
                    
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
        print(f"Executed: {' '.join(command)} in {cwd}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        print(f"Command failed: {e}")
        raise

def _update_ant_version(path, version, version_file):
    """Updates the Ant project version."""
    version_file_path = _find_file(path, version_file)
    with open(version_file_path, 'r') as file:
        content = file.read()
    content = re.sub(r'(?m)^\s*version\s*=\s*.*$', f'version = {version}', content)
    with open(version_file_path, 'w') as file:
        file.write(content)
    print(f"Updated Ant version in {version_file_path} to {version}")
    logging.info(f"Updated Ant version in {version_file_path} to {version}")

def _update_angular_version(path, version, version_file):
    """Updates the Angular project version."""
    version_file_path = _find_file(path, version_file)
    with open(version_file_path, 'r') as file:
        content = file.read()
    content = re.sub(r'"version"\s*:\s*".*?"\s*,', f'"version": "{version}",', content)
    with open(version_file_path, 'w') as file:
        file.write(content)
    print(f"Updated Angular version in {version_file_path} to {version}")
    logging.info(f"Updated Angular version in {version_file_path} to {version}")
    
def checkout_and_pull(project_filter = ''):
    """Performs git checkout on master and pulls latest changes."""
    with open("release_handler_config.yaml", "r") as file:
        config = yaml.safe_load(file)   
    try:
        for project in config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue  
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            if click.confirm(f"Check out and pull project {project['name']}?", default=True):
                branch = project["git_branch"]
                _execute_command(["git", "checkout", branch], project['project_path'])
                _execute_command(["git", "pull"], project['project_path'])
                logging.info(f"Project {project['name']} checked out and pulled")  
                print(f"Project {project['name']} checked out and pulled")
    except Exception as e:
        logging.error(f"An error occurred: {e}")  
        print(f"An error occurred: {e}")

def update_versions(project_filter = ''):
    """Reads the YAML file and processes each project."""
    with open("release_handler_config.yaml", "r") as file:
        config = yaml.safe_load(file)
    
    try:
        for project in config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue  
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            if click.confirm(f"Update version for project {project['name']}?", default=True):
                if project["type"] == "Maven":
                    _update_all_pom_properties(project, config)
                    _update_maven_versions_from_yaml(project, config)
                elif project["type"] == "Ant":
                    _update_ant_version(project["project_path"], project["version"], project["version_file"])
                elif project["type"] == "Angular":
                    _update_angular_version(project["project_path"], project["version"], project["version_file"])
    except Exception as e:
        logging.error(f"An error occurred: {e}")  
        print(f"An error occurred: {e}") 
    
def create_tags(project_filter = ''):
    """Tags each project with the appropriate tag name."""
    try:
        with open("release_handler_config.yaml", "r") as file:
            config = yaml.safe_load(file)
            resolved_config = _resolve_placeholders(config)
        
        for project in resolved_config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue  
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            tag = project["tag"]
            if click.confirm(f"Create tag {tag} for project {project['name']}?", default=True):
                if _is_tag_committed(tag, project["project_path"]):
                    logging.info(f"Tag {tag} of project {project['name']} already commited")
                    print(f"Tag {tag} of project {project['name']} already commited")
                    continue
                _execute_command(["git", "tag", tag], project["project_path"])
                logging.info(f"Tagged {project['name']} with {tag}")
                print(f"Tagged {project['name']} with {tag}")
    except Exception as ex:
        logging.error(f"An error occurred: {ex}")  
        print(f"An error occurred: {ex}")
        
        
def push_tags(project_filter = ''):
    try:
        with open("release_handler_config.yaml", "r") as file:
            config = yaml.safe_load(file)
            resolved_config = _resolve_placeholders(config)
        
        for project in resolved_config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue  
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            tag = project["tag"]
            if click.confirm(f"Push tag {tag} for project {project['name']}?", default=True):
                try:
                    if _is_tag_pushed(project["project_path"], tag):
                        logging.info(f"The {tag} for project {project['name']} is already pushed")
                        print(f"The {tag} for project {project['name']} is already pushed")
                        continue
                    _execute_command(["git", "push", "origin", "tag", tag], project["project_path"])
                except Exception as e:
                    pass
                logging.info(f"Pushed tag {tag} for project {project['name']}")
                print(f"Pushed tag {tag} for project {project['name']}")
    except Exception as ex:
        logging.error(f"An error occurred: {ex}")  
        print(f"An error occurred: {ex}")
                
def delete_tags(project_filter = ''):
    """Delete tag of each project with the appropriate tag name."""
    try:
        with open("release_handler_config.yaml", "r") as file:
            config = yaml.safe_load(file)
            resolved_config = _resolve_placeholders(config)
        
        for project in resolved_config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue  
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            tag = project["tag"]
            if click.confirm(f"Delete tag {tag} for project {project['name']}?", default=True):
                if not _is_tag_committed(tag, project["project_path"]):
                    logging.info(f"There is no tag {tag} for project {project['name']}")
                    print(f"There is no tag {tag} for project {project['name']}")
                    continue
                _execute_command(["git", "tag", "-d", tag], project["project_path"])
                logging.info(f"Deleted tag {tag}")
                print(f"Deleted tag {tag}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")  
        print(f"An error occurred: {e}") 
        
def delete_tags_remotely(project_filter = ''):
    """Delete tag of each project with the appropriate tag name."""
    try:
        with open("release_handler_config.yaml", "r") as file:
            config = yaml.safe_load(file)
            resolved_config = _resolve_placeholders(config)
        
        remote = config["remote_git_repo"]
        print(f"remote repo {remote}")
        if not remote:
            remote = "origin"
        print(f"project_filter {project_filter}")
        for project in resolved_config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue  
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            tag = project["tag"]
            if click.confirm(f"Delete tag {tag} remotely for project {project['name']}?", default=True):
                if not _is_tag_pushed(project["project_path"], tag):
                    logging.info(f"The {tag} for project {project['name']} does not exist remotely")
                    print(f"The {tag} for project {project['name']} does not exist remotely")
                    continue
                _execute_command(["git", "push", "--delete", remote, tag], project["project_path"])
                logging.info(f"Deleted tag {tag} remotely")
                print(f"Deleted tag {tag} remotely")
    except Exception as e:
        logging.error(f"An error occurred: {e}")  
        print(f"An error occurred: {e}") 
        
def commit(project_filter = ''):
    """Commits changes for each project with confirmation."""
    try:
        with open("release_handler_config.yaml", "r") as file:
            config = yaml.safe_load(file)
        
        for project in config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue  
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            changes =_list_git_changes(project["project_path"])
            logging.info(f"Changes to commit {changes}")
            print(f"Changes to commit {changes}")
            if click.confirm(f"Commit changes for project {project['name']}?", default=False):
                _execute_command(["git", "commit", "-am", f"Update project with version {project['version']}"] , project["project_path"])
                logging.info(f"Update project with version {project['version']}")
                print(f"Update project with version {project['version']}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")  
        print(f"An error occurred: {e}") 
        
def remove_last_commit(project_filter = ''):
    """Resets the last commit based on reset-type."""
    try:
        with open("release_handler_config.yaml", "r") as file:
            config = yaml.safe_load(file)
        
        for project in config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue              
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            if click.confirm(f"Reset last commit for {project['name']}?", default=False):
                if not _is_last_commit_pushed(project["project_path"]):
                    _execute_command(["git", "reset", f"--{project['reset_type']}", "HEAD~1"] , project["project_path"])
                    logging.info(f"Resetted last commit for project {project['name']}")
                    print(f"Resetted last commit for project {project['name']}")
                else:
                    logging.info(f"Reset aborted because the last commit for project {project['name']} was already pushed")
                    print(f"Reset aborted because the last commit for project {project['name']} was already pushed")
    except Exception as e:
        logging.error(f"An error occurred: {e}")  
        print(f"An error occurred: {e}") 

def reset(project_filter = ''):
    """Resets projects based on reset-type."""
    try:
        with open("release_handler_config.yaml", "r") as file:
            config = yaml.safe_load(file)
        
        for project in config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue  
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            if click.confirm(f"Reset {project['name']}?", default=True):
                _execute_command(["git", "reset", f"--{project['reset_type']}"] , project["project_path"])
                logging.info(f"Resetted project {project['name']}")
                print(f"Resetted project {project['name']}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")  
        print(f"An error occurred: {e}") 
               
def compile_check(project_filter = ''):
    """Resets projects based on reset-type."""
    try:
        with open("release_handler_config.yaml", "r") as file:
            config = yaml.safe_load(file)
            
        for project in config["projects"]:
            if project_filter != '' and project_filter != project['name']:
                continue        
            if 'skip' in project and project['skip']:
                logging.info(f"Project {project['name']} is configured to be skipped")
                print(f"Project {project['name']} is configured to be skipped")
                continue
            if click.confirm(f"Compile {project['name']}?", default=True):
                logging.info(f"Compiling project {project['name']} ...")
                print(f"Compiling {project['name']} ...")
                if project["type"] == "Maven":
                    if _compile_maven_project(project["project_path"], config["maven_home"], config["maven_settings"], config):
                        logging.info(f"Maven project {project['name']} compiled successfully")
                        print(f"Maven project {project['name']} compiled successfully")
                elif project["type"] == "Angular":
                    if _compile_angular_project(project["project_path"], config):
                        logging.info(f"Angular project {project['name']} compiled successfully")
                        print(f"Angular project {project['name']} compiled successfully")
                elif project["type"] == "Ant":
                    if _compile_ant_project(project["project_path"], config):
                        logging.info(f"Ant project {project['name']} compiled successfully")
                        print(f"Ant project {project['name']} compiled successfully")                                      
    except Exception as e:
        logging.error(f"An error occurred: {e}")  
        print(f"An error occurred: {e}") 
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "update_versions":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                update_versions(sys.argv[2])
            else:
                update_versions()
        elif sys.argv[1] == "create_tags":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                create_tags(sys.argv[2])
            else:
                create_tags()
        elif sys.argv[1] == "delete_tags":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                delete_tags(sys.argv[2])
            else:
                delete_tags()
        elif sys.argv[1] == "delete_tags_remotely":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                delete_tags_remotely(sys.argv[2])
            else:
                delete_tags_remotely()
        elif sys.argv[1] == "push_tags":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                push_tags(sys.argv[2])
            else:
                push_tags()    
        elif sys.argv[1] == "commit":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                commit(sys.argv[2])
            else:
                commit()                  
        elif sys.argv[1] == "remove_last_commit":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                remove_last_commit(sys.argv[2])
            else:
                remove_last_commit() 
        elif sys.argv[1] == "reset":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                reset(sys.argv[2])
            else:
                reset() 
        elif sys.argv[1] == "checkout_and_pull":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                checkout_and_pull(sys.argv[2])
            else:
                checkout_and_pull()   
        elif sys.argv[1] == "compile_check":
            if len(sys.argv) > 2 and sys.argv[2] != "":
                compile_check(sys.argv[2])
            else:
                compile_check()            
        else:
             print("Wrong argument!")           
    else:
        raise ValueError("No arguments provided! Usage: release_handler.py <one of update_versions, create_tags, delete_tags, delete_tags, commit, remove_last_commit, reset, checkout_and_pull, compile_check>")