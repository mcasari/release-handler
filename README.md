# release-handler
Python program with functions aimed at handling versioning and tagging of Maven, Ant and Angular projects 

pip install pyyaml
pip install click

You can execute the script with different commands:

python release_handler.py projects.yaml process_projects
python release_handler.py projects.yaml tag_projects
python release_handler.py projects.yaml commit_projects
python release_handler.py projects.yaml push_projects
python release_handler.py projects.yaml reset_lastcommit

This script automates version updates, tagging, committing, and pushing, ensuring logging and user confirmation where needed.



