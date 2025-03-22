# release-handler

Python script named release_handler.py with functions aimed at handling versioning and check compilation of a configured set of Maven, Ant and Angular projects. It also allows to perform several Git operations on all the projects like commit, checkout, pull and reset. The projects are configured in a release_handler.yaml file.

## Prerequisites

To use the script you must have Python installed. You can go to the Python dowload page https://www.python.org/downloads/ and follow the instructions 
to install the latest version in your specific operating system.

When running the program some of libraries imported in the release_handler.py script could not available at runtime. You can install the missing libraries running commands like the following
in the command line:

'pip install click'


## How the script works

The release_handler.py script defines the following functions:

- update_versions
- create_tags
- delete_tags
- commit
- remove_last_commit
- reset
- checkout_and_pull
- compile_check

```
environment: TEST
release_notes:
  - "Note 1"
  - "Note 2"
maven_home: C:/APPLICATIONS/apache-maven-3.9.6
maven_settings: C:/Users/macasari/.m2/settingsCSI.xml
maven_compile_options:
    - "-Dpostfix=''"
    - "-DskipTests"  
maven_namespace: http://maven.apache.org/POM/4.0.0
nodejs_home: C:/Program Files/nodejs
nodejs_compile_options:
    - "--configuration=prod-rp-01" 
ant_home: C:/APPLICATIONS/apache-ant-1.6.2_ivy2
ant_target: distribution 
ant_compile_options:
    - "-Dtarget=prod-rp-01" 
projects:
  - name: mavenproject
    project_path: C:\eclipse-workspaces\csi\mavenproject
    type: Maven
    version: 1.21.0
    version_file: pom.xml
    tag: "{environment}-1.21.0-001"
    reset_type: hard
    parent_version: 1.21.0
    properties:
      - property_name: tar.version
        property_value: 1.21.0
    dependencies:
      - dependency_name: mavenproject-ear
        dependency_version: 1.21.0
      - dependency_name: mavenproject-jar
        dependency_version: 1.21.0
      - dependency_name: mavenproject-web
        dependency_version: 1.21.0      
  - name: angularproject
    project_path: C:\eclipse-workspaces\csi\angularproject
    type: Angular
    version: 1.21.0
    version_file: package.json
    tag: "{environment}-1.21.0-001"
    reset_type: hard  
  - name: antproject
    project_path: C:\eclipse-workspaces\csi\antproject
    type: Ant
    version: 1.2.2
    version_file: build.properties
    tag: "{environment}-1.21.0-001"
    reset_type: hard
```




You can execute the script with different commands:

python release_handler.py projects.yaml process_projects
python release_handler.py projects.yaml tag_projects
python release_handler.py projects.yaml commit_projects
python release_handler.py projects.yaml push_projects
python release_handler.py projects.yaml reset_lastcommit

This script automates version updates, tagging, committing, and pushing, ensuring logging and user confirmation where needed.

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.


