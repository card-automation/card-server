import base64
import importlib.resources
import io
import json
import tempfile
import threading
import time
import zipfile
from datetime import timedelta
from importlib.resources import as_file
from pathlib import Path
from typing import Union, TypedDict, Required, Optional

from githubkit import GitHub, AppAuthStrategy, AppInstallationAuthStrategy
from githubkit.exception import RequestFailed
from githubkit.versions.v2022_11_28.models import Installation, Repository, PullRequestSimple, Commit, Deployment

from card_auto_add.config import Config, _HasCommitVersions
from card_auto_add.workers.events import WorkerEvent, ApplicationRestartNeeded
from card_auto_add.workers.utils import EventsWorker


# These worker events are only for this worker, to make some of the threading logic easier
class NewGitHubInstallation(WorkerEvent):
    def __init__(self, install_id: int):
        self._install_id = install_id

    @property
    def install_id(self) -> int:
        return self._install_id


class ApplicationUpdateAvailable(WorkerEvent):
    def __init__(self, commit: str):
        self._commit = commit

    @property
    def commit(self) -> str:
        return self._commit


_Events = Union[
    NewGitHubInstallation,
    ApplicationUpdateAvailable
]


class _AppInstall(TypedDict):
    install_id: Required[int]
    owner: Required[str]
    repos: Required[list[str]]


class GitHubWatcher(EventsWorker[_Events]):
    def __init__(self, config: Config):
        super().__init__()
        self._config = config

        self._known_installs_file = importlib.resources.files('card_auto_add').joinpath('known_github_installs.json')

        self._known_installs: list[_AppInstall] = json.loads(self._known_installs_file.read_text())
        self._rejected_installs: set[int] = set()
        self._pending_installs: dict[int, int] = {}  # install id -> GitHub PR

        with config.github.private_key_path.open('r') as fh:
            self.__private_key = fh.read()

        app_auth = AppAuthStrategy(
            app_id=config.github.app_id,
            private_key=self.__private_key
        )
        self._github_app: GitHub = GitHub(app_auth)

        self._github_installs: dict[int, GitHub] = {}
        self._install_owners: dict[int, str] = {}

        self._self_install_id = config.github.self_installation_id
        install_auth = AppInstallationAuthStrategy(
            self._config.github.app_id, self.__private_key, self._self_install_id
        )
        self._github_self: GitHub = GitHub(install_auth)
        my_install: _AppInstall = [x for x in self._known_installs if x["install_id"] == self._self_install_id][0]
        self._known_installs.remove(my_install)  # We handle the main installation differently
        self._self_owner = my_install["owner"]
        self._self_repo = my_install["repos"][0]
        self._self_default_branch = self._github_self.rest.repos.get(self._self_owner,
                                                                     self._self_repo).parsed_data.default_branch

        self._deployment_in_progress: threading.Event = threading.Event()

        self._complete_application_deployments()

        self._call_every(timedelta(minutes=1), self._check_for_new_installations)
        self._call_every(timedelta(minutes=1), self._check_for_app_updates)

    def _handle_event(self, event: _Events):
        if isinstance(event, NewGitHubInstallation):
            self._handle_new_github_installation(event)

        if isinstance(event, ApplicationUpdateAvailable):
            self._handle_application_update_available(event)

    def _check_for_new_installations(self) -> None:
        install: Installation
        for install in self._github_app.paginate(self._github_app.rest.apps.list_installations):
            if install.id not in self._install_owners:
                self._install_owners[install.id] = install.account.login

            if install.id == self._self_install_id:
                # This is the main application, ignore it
                continue

            # Let's make sure we have a reference to this installation. We will need it later.
            if install.id not in self._github_installs:
                install_auth = AppInstallationAuthStrategy(
                    self._config.github.app_id, self.__private_key, install.id
                )
                self._github_installs[install.id] = GitHub(install_auth)

            if install.id in self._rejected_installs:
                # We've rejected this install, ignore it
                continue

            if any(x['install_id'] == install.id for x in self._known_installs):
                # This is a good install
                continue

            self._outbound_event_queue.put(NewGitHubInstallation(
                install_id=install.id
            ))

    def _handle_new_github_installation(self, event: NewGitHubInstallation):
        branch_name = f"install-{event.install_id}"

        pr: PullRequestSimple
        for pr in self._github_self.rest.pulls.list(
                owner=self._self_owner,
                repo=self._self_repo,
                state="all",
                head=f"{self._self_owner}:{branch_name}"
        ).parsed_data:
            if pr.state == "open":
                # Nothing to do here. This does mean we'll get the event every loop, but that's perfectly fine.
                return

            if any([l.name == "rejected-plugin" for l in pr.labels]):
                self._rejected_installs.add(event.install_id)
                return  # We rejected this PR, goodbye

        # At this point, we have no PR that we consider valid for decision-making purposes. Let's create one.

        # Let's look up all the repos we have access to. We need it both for the PR and potentially the json file update
        gh: GitHub = self._github_installs[event.install_id]

        plugin_repos: list[str] = []
        repo: Repository
        for repo in gh.paginate(
                gh.rest.apps.list_repos_accessible_to_installation,
                map_func=lambda r: r.parsed_data.repositories
        ):
            plugin_repos.append(repo.name)

        # Let's go find an existing branch and delete it if it's there
        try:
            # Test to see if the branch exists. Will throw a 404 if it doesn't and continue on if it does.
            self._github_self.rest.repos.get_branch(
                owner=self._self_owner,
                repo=self._self_repo,
                branch=branch_name
            )

            self._github_self.rest.git.delete_ref(
                owner=self._self_owner,
                repo=self._self_repo,
                ref=f"heads/{branch_name}"
            )
        except RequestFailed as ex:
            if ex.response.status_code != 404:
                raise  # We expect not to find it, we don't expect to have any other issues

        # The branch shouldn't exist now, so let's create it
        self._github_self.rest.git.create_ref(
            owner=self._self_owner,
            repo=self._self_repo,
            data={
                "ref": f"refs/heads/{branch_name}",
                # This might not match our latest commit if we push an update but this runs before it's deployed.
                # We can fix that but constantly asking "what's our latest commit", but there will always be some
                # risk of race condition.
                "sha": self._config.deploy.commit,
            }
        )

        # Read it from the file to guarantee its contents, since we mess with it in __init__.
        known_installs: list[_AppInstall] = json.loads(self._known_installs_file.read_text())
        json_file_path: Path
        with as_file(self._known_installs_file) as f:
            json_file_path = f.relative_to(self._config.deploy.root)

        owner_login = self._install_owners[event.install_id]
        known_installs.append({
            "install_id": event.install_id,
            "owner": owner_login,
            "repos": plugin_repos
        })

        known_installs = sorted(known_installs, key=lambda x: x['install_id'])  # Sort them in install id order

        install_content = json.dumps(known_installs, indent=2)

        self._github_self.graphql \
            .request(query="mutation ($input: CreateCommitOnBranchInput!) {"
                           "  createCommitOnBranch(input: $input) {"
                           "    commit {"
                           "      url"
                           "    }"
                           "  }"
                           "}",
                     variables={
                         "input": {
                             "branch": {
                                 "repositoryNameWithOwner": f"{self._self_owner}/{self._self_repo}",
                                 "branchName": branch_name
                             },
                             "message": {
                                 "headline": "Install"
                             },
                             "fileChanges": {
                                 "additions": [
                                     {
                                         "path": str(json_file_path),
                                         "contents": base64.b64encode(install_content.encode('ascii'))
                                     }
                                 ]
                             },
                             "expectedHeadOid": self._config.deploy.commit
                         }
                     }
                     )

        pr_body = "The following repos are currently seen by the installation:\n"
        for repo in plugin_repos:
            url = f"https://github.com/{owner_login}/{repo}"
            pr_body += f"- [{owner_login}/{repo}]({url})\n"

        pr_body += "\n\n"
        pr_body += "If these repos are incorrect, follow these steps:\n"
        pr_body += "1. Fix the permissions for the GitHub app to only have access to the plugins you expect\n"
        pr_body += "2. Mark this PR as closed, but do NOT label it as \"rejected-plugin\"\n"

        self._github_self.rest.pulls.create(
            owner=self._self_owner,
            repo=self._self_repo,
            data={
                "title": f"Confirm install {event.install_id} for {owner_login}",
                "head": branch_name,
                "base": "main",  # TODO Don't hardcode
                "body": pr_body
            }
        )

    def _check_for_app_updates(self) -> None:
        if self._deployment_in_progress.is_set():
            return

        # TODO NOTE We can refactor this to return an updated commit or None for a given owner, repo, and "has commit versions".
        # Then we can decide what event to put in the queue.
        # All of this is so similar, that I'm very tempted to refactor it again and don't directly differentiate between
        # plugin and app updates.
        latest_commit: Commit = self._github_self.rest.repos.list_commits(
            owner=self._self_owner,
            repo=self._self_repo,
            per_page=1
        ).parsed_data[0]

        if self._config.deploy.commit == latest_commit.sha:
            # No update needed
            return

        # TODO Check for commit status to make sure any actions are done

        self._outbound_event_queue.put(ApplicationUpdateAvailable(
            commit=latest_commit.sha
        ))

    def _handle_application_update_available(self, event: ApplicationUpdateAvailable):
        self._deploy_update(
            github=self._github_self,
            repo_owner=self._self_owner,
            repo_name=self._self_repo,
            commit=event.commit,
            has_commit_versions=self._config.deploy,
            environment=self._config.deploy.environment
        )

    def _deploy_update(self,
                       github: GitHub,
                       repo_owner: str,
                       repo_name: str,
                       commit: str,
                       has_commit_versions: _HasCommitVersions,
                       environment: str):
        self._deployment_in_progress.set()

        deployments = github.rest.repos.list_deployments(
            owner=repo_owner,
            repo=repo_name,
            sha=commit,
            environment=environment
        ).parsed_data

        # No started deployments, definitely deploy
        should_deploy = len(deployments) == 0
        our_deployment: Optional[Deployment] = None
        in_progress = False

        for deployment in deployments:
            statuses = github.rest.repos.list_deployment_statuses(
                owner=repo_owner,
                repo=repo_name,
                deployment_id=deployment.id,
            ).parsed_data
            if len(statuses) == 0:
                our_deployment = deployment
                should_deploy = True
                break  # It's queued, we can work with this

            for status in statuses:
                # If it succeeded, we shouldn't have even been told about it.
                # TODO Decide on if that's an error condition for "production" environment
                # If it failed, a new commit will probably be pushed
                if status.state in ["success", "failure"]:
                    should_deploy = False
                    break

                if status.state == "in_progress":
                    our_deployment = deployment
                    in_progress = True
                    should_deploy = True

        if not should_deploy:
            return

        if len(deployments) == 0:
            our_deployment = github.rest.repos.create_deployment(
                owner=repo_owner,
                repo=repo_name,
                data={
                    "ref": commit,
                    "environment": environment
                }
            ).parsed_data

        if not in_progress:
            print("Marking as in progress")
            github.rest.repos.create_deployment_status(
                owner=repo_owner,
                repo=repo_name,
                deployment_id=our_deployment.id,
                state="in_progress",
                environment=environment,
            )

        zip_content = github.rest.repos.download_zipball_archive(
            owner=repo_owner,
            repo=repo_name,
            ref=commit,
        ).content

        deploy_directory = has_commit_versions.root_path / "versions" / commit
        deploy_directory.mkdir(parents=True, exist_ok=True)

        # Extract the zip file the way we want it extracted
        with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zf:
            for zip_info in zf.infolist():
                # The zip file has an outer directory we don't want, so we get the new relative path without it
                zip_path = Path(zip_info.filename)
                relative_path = Path(*zip_path.parts[1:])
                full_path = (deploy_directory / relative_path).resolve()

                if zip_info.is_dir():
                    full_path.mkdir(parents=True, exist_ok=True)
                    continue

                with full_path.open('wb') as fh:
                    fh.write(zf.read(zip_info.filename))

        current_path = has_commit_versions.current_path
        if current_path.exists(follow_symlinks=False):
            current_path.unlink()

        has_commit_versions.commit = commit
        self._config.write()

        # The current path will be re-created with the new commit the next time it's accessed

        self._outbound_event_queue.put(ApplicationRestartNeeded())  # Tell the worker event loop to stop everything

    def _complete_application_deployments(self):
        self._complete_deployment_for_repo(
            github=self._github_self,
            repo_owner=self._self_owner,
            repo_name=self._self_repo,
            commit=self._config.deploy.commit,
            environment=self._config.deploy.environment
        )

    @staticmethod
    def _complete_deployment_for_repo(github: GitHub,
                                      repo_owner: str,
                                      repo_name: str,
                                      commit: str,
                                      environment: str):
        deployments = github.rest.repos.list_deployments(
            owner=repo_owner,
            repo=repo_name,
            sha=commit,
            environment=environment
        ).parsed_data

        for deployment in deployments:
            should_mark_success = False

            statuses = github.rest.repos.list_deployment_statuses(
                owner=repo_owner,
                repo=repo_name,
                deployment_id=deployment.id,
            ).parsed_data
            for status in statuses:
                if status.state == "in_progress":
                    should_mark_success = True
                elif status.state in ["success", "failure"]:
                    should_mark_success = False
                    break

            if should_mark_success:
                github.rest.repos.create_deployment_status(
                    owner=repo_owner,
                    repo=repo_name,
                    deployment_id=deployment.id,
                    state="success",
                    environment=deployment.environment,
                )
