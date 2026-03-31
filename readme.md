# Card Auto Add

The goal of this project is to automatically add member cards to a WinDSX database. It runs on startup and uses the WinDSX API to talk to the system. This system was designed for the access control system at a single building, it was not designed for use by others.  


## Instructions:
Our goal is to create a Windows "service" (not an actual service) that can run in the background on a machine running WinDSX and add cards without any user interaction. We write to the database directly and support plugins to handle the actual logic of updates.


## Writing a Plugin

### Scaffold a new plugin

Install [copier](https://copier.readthedocs.io/) via `uv` and scaffold from the template:

```bash
uvx copier copy gh:card-automation/card-plugin-template .
```

You will be prompted for:
- **GitHub owner** — your GitHub username or organization
- **GitHub repo** — defaults to `<owner>-card-access`
- **Python package name** — defaults to the repo name with dashes replaced by underscores
- **Plugin class name** — defaults to `Load<Owner>Plugin`

### Register your repo

For the card automation server to watch and deploy your plugin, install the GitHub app on your repo:

[https://github.com/apps/windsx-card-automation-server](https://github.com/apps/windsx-card-automation-server)

### Development setup

From your plugin directory:

```bash
uv sync
uv run pytest
```