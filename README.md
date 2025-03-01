# Python Asynchronous Input Output (AIO) Artifactory

Python Asynchronous Input Output (AIO) Artifactory

## Table of Content

* [JFrog Command Line Interface (CLI) Example](#jfrog-command-line-interface-cli-example)
    * [Deploy One File](#deploy-one-file)
        * [Command](#command)
        * [Output](#output)
        * [Result](#result)
    * [Retrieve One File](#retrieve-one-file)
        * [Command](#command-1)
        * [Output](#output-1)
        * [Result](#result-1)
* [Glossary](#glossary)
* [Reference](#reference)
    * [Artifactory](#artifactory)
    * [Visual Studio Code](#visual-studio-code)

## JFrog Command Line Interface (CLI) Example

### Deploy One File

#### Command

```bash
# Short
jf rt u /root/folder/subfolder/file.ext generic-repository[-local]/

# Long
jfrog rt upload /root/folder/subfolder/file.ext generic-repository[-local]/
```

#### Output

```text
15:54:51 [🔵Info] Log path: /Users/user/.jfrog/logs/jfrog-cli.2025-02-21.15-54-51.52108.log
15:54:51 [🔵Info] These files were uploaded:

📦 generic-repository[-local]
└── 📁 root
    └── 📁 folder
        └── 📁 subfolder
            └── 📄 file.ext


{
  "status": "success",
  "totals": {
    "success": 1,
    "failure": 0
  }
}
```

#### Result

```text
generic-repository[-local]/
│
└── root/
    └── folder/
        └── subfolder/
            └── file.ext
```

### Retrieve One File

#### Command

```bash
# Short
jf rt dl generic-repository[-local]/folder/subfolder/file.ext

# Long
jfrog rt download generic-repository[-local]/folder/subfolder/file.ext
```

#### Output

```text
15:43:59 [🔵Info] Log path: /Users/user/.jfrog/logs/jfrog-cli.2025-02-21.15-43-59.51631.log
{
  "status": "success",
  "totals": {
    "success": 1,
    "failure": 0
  }
}
```

#### Result

```text
folder/
│
└── subfolder/
    └── file.ext
```

## Glossary

### Local Path

The Local Path is represented by a file system path pointing to a
location on the local file system.

#### Example

```text
# Unix
/home/user/path/subpath/
```

```text
# Windows
C:\Users\user\path\subpath\
```

### Remote Path

The Remote Path is represented by a URL (Uniform Resource Locator)
pointing to a location on the Internet. It should be the URL for
Artifactory.

#### Example

```text
https://artifactory.acme.com/artifactory/repository/path/subpath/
```

## Reference

### Artifactory

* [Artifactory Query Language](https://jfrog.com/help/r/jfrog-artifactory-documentation/artifactory-query-language)
    * [Artifactory AQL Entity and Field](https://jfrog.com/help/r/jfrog-artifactory-documentation/aql-entities-and-fields)
* [Artifactory REST APIs](https://jfrog.com/help/r/jfrog-rest-apis/artifactory-rest-apis)
    * [Artifactory REST APIs SEARCHES](https://jfrog.com/help/r/jfrog-rest-apis/searches)
        * [Artifactory Maximum Number of Search Queries](https://jfrog.com/help/r/maximum-number-of-search-queries/maximum-number-of-search-queries.)
    * [Deploy Artifact APIs](https://jfrog.com/help/r/jfrog-rest-apis/deploy-artifact-apis)

### Visual Studio Code

* [pytest configuration settings](https://code.visualstudio.com/docs/python/testing#_pytest-configuration-settings)
