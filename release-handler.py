import yaml
import subprocess
import logging
import os
import click

def _run_command(command, cwd):
    """Runs a shell command in the given working directory."""
    process = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if process.returncode != 0:
        logging.error(f"Command failed: {command}\n{process.stderr}")
    return process

def _update_maven_version(path, version):
    """Updates Maven project version and dependencies."""
    logging.info(f"Updating Maven project at {path} to version {version}")
    _run_command(f'mvn versions:set -DnewVersion={version} -DgenerateBackupPoms=false', path)

def _update_ant_version(path, version, version_file):
    """Updates Ant project version in the specified version file."""
    logging.info(f"Updating Ant project at {path} to version {version} in {version_file}")
    version_file_path = os.path.join(path, version_file)
    with open(version_file_path, 'r') as file:
        content = file.read()
    content = content.replace('version=', f'version={version}')
    with open(version_file_path, 'w') as file:
        file.write(content)

def _update_angular_version(path, version, version_file):
    """Updates Angular project version in the package.json or other specified file."""
    logging.info(f"Updating Angular project at {path} to version {version} in {version_file}")
    version_file_path = os.path.join(path, version_file)
    with open(version_file_path, 'r') as file:
        content = file.read()
    content = content.replace('"version":', f'"version": "{version}"')
    with open(version_file_path, 'w') as file:
        file.write(content)

def _checkout_and_pull(path):
    """Checks out the master branch and pulls the latest changes."""
    logging.info(f"Checking out master and pulling latest changes for {path}")
    _run_command('git checkout master', path)
    _run_command('git pull', path)

def update_projects_versions():
    """Reads the YAML config and processes each project."""
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    for project in config['projects']:
        _checkout_and_pull(project['folder'])
        if project['type'] == 'Maven':
            _update_maven_version(project['folder'], project['version'])
        elif project['type'] == 'Ant':
            _update_ant_version(project['folder'], project['version'], project['version_file'])
        elif project['type'] == 'Angular':
            _update_angular_version(project['folder'], project['version'], project['version_file'])

def tag_projects():
    """Tags each project with the configured tag name."""
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    for project in config['projects']:
        logging.info(f"Tagging {project['folder']} with {project['tag']}")
        _run_command(f'git tag {project["tag"]}', project['folder'])

def commit_projects():
    """Commits changes for each project with confirmation."""
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    for project in config['projects']:
        if click.confirm(f"Commit changes for {project['folder']}?"):
            logging.info(f"Committing changes for {project['folder']}")
            _run_command('git commit -am "Updating project version"', project['folder'])

def push_projects():
    """Pushes changes for each project with confirmation."""
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    for project in config['projects']:
        if click.confirm(f"Push changes for {project['folder']}?"):
            logging.info(f"Pushing changes for {project['folder']}")
            _run_command('git push', project['folder'])

def reset_lastcommit():
    """Resets the last commit for each project based on reset type."""
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    for project in config['projects']:
        if click.confirm(f"Reset last commit for {project['folder']} ({project['reset-type']})?"):
            logging.info(f"Resetting last commit for {project['folder']} with {project['reset-type']} mode")
            _run_command(f'git reset --{project["reset-type"]} HEAD~1', project['folder'])

if __name__ == "__main__":
    logging.basicConfig(filename='release-handler.log', level=logging.INFO, format='%(asctime)s - %(message)s')
    cli = click.Group()
    cli.add_command(click.Command('update_projects_versions', callback=process_projects))
    cli.add_command(click.Command('tag_projects', callback=tag_projects))
    cli.add_command(click.Command('commit_projects', callback=commit_projects))
    cli.add_command(click.Command('push_projects', callback=push_projects))
    cli.add_command(click.Command('reset_lastcommit', callback=reset_lastcommit))
    cli()
