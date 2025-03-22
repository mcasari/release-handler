# release-handler

Python script named release_handler.py with functions aimed at handling versioning and Git committing, pulling, resetting of a configured set of Maven, Ant and Angular projects. 
The projects are configured in a release_handler.yaml file.

## Prerequisites

To use the script you must have Python installed. You can go to the Python dowload page https://www.python.org/downloads/ and follow the instructions 
to install the latest version in your specific operating system.

When running the program some of libraries imported in the release_handler.py script could not available at runtime. You can install the missing libraries running commands like the following
in the command line:

'pip install click'


## How the script works

You can execute the script with different commands:

python release_handler.py projects.yaml process_projects
python release_handler.py projects.yaml tag_projects
python release_handler.py projects.yaml commit_projects
python release_handler.py projects.yaml push_projects
python release_handler.py projects.yaml reset_lastcommit

This script automates version updates, tagging, committing, and pushing, ensuring logging and user confirmation where needed.

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.


