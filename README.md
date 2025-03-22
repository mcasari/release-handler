# release-handler

Python script named release_handler.py with functions aimed at handling versioning, tagging and check compilation of a configured set of Maven, Ant and Angular projects. It also allows to perform several Git operations on all the projects like commit, checkout, pull and reset. The projects are configured in a release_handler.yaml file.

## Prerequisites

To use the script you must have Python installed. You can go to the Python dowload page https://www.python.org/downloads/ and follow the instructions 
to install the latest version in your specific operating system.

When running the program some of libraries imported in the release_handler.py script could not available at runtime. You can install the missing libraries running commands like the following
in the command line:

'pip install click'


## How the script works

The release_handler.py script defines the following functions:

- update_versions: updates the versions of each projects with the values read on the configuration file
- create_tags: creates tag for each project with the configured tag name
- delete_tags: deletes on each project the tag named as in the configuration file, to perform a rollback on the tag operation
- commit: performs a Git commit on each project
- remove_last_commit: removes the last commit on each project, to rollback the commit operation defined above
- reset: performs a Git reset on each project with type hard, soft or mixed, according to the value set in the configuration file
- checkout_and_pull: performs a checkout on the branch defined in the configuration file and a pull from the remote Git repository
- compile_check: performs a compilation of each project to check possible errors using the environment settings defined in the configuration file

Here is an example of the configuration file content:

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
    git_branch: master
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
    git_branch: master
  - name: antproject
    project_path: C:\eclipse-workspaces\csi\antproject
    type: Ant
    version: 1.2.2
    version_file: build.properties
    tag: "{environment}-1.21.0-001"
    reset_type: hard
    git_branch: master
```

You can execute each funtion with a command like this, provided that the release_handler.yaml file is in the same directory of the script:

`python release_handler.py update_versions`

or in a shorter way:

`release_handler.py update_versions`

