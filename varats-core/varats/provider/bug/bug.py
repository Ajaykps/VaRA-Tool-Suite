"""Bug Classes used by bug_provider."""

import re
import typing as tp

import pygit2
from github import Github
from github.IssueEvent import IssueEvent
from github.PaginatedList import PaginatedList
from github.Repository import Repository

from varats.project.project_util import (
    get_local_project_git_path,
    get_local_project_git,
)
from varats.utils.github_util import get_cached_github_object_list


class PygitBug:
    """Bug representation using the ``pygit2.Commit`` class."""

    def __init__(
        self, fixing_commit: pygit2.Commit,
        introducing_commits: tp.List[pygit2.Commit], issue_id: tp.Optional[int]
    ) -> None:
        self.__fixing_commit = fixing_commit
        self.__introducing_commits = introducing_commits
        self.__issue_id = issue_id

    @property
    def fixing_commit(self) -> pygit2.Commit:
        """Commit fixing the bug as pygit2 Commit."""
        return self.__fixing_commit

    @property
    def introducing_commits(self) -> tp.List[pygit2.Commit]:
        """Commits introducing the bug as List of pygit2 Commits."""
        return self.__introducing_commits

    @property
    def issue_id(self) -> tp.Optional[int]:
        """ID of the issue associated with the bug, if there is one."""
        return self.__issue_id

    def __eq__(self, other) -> bool:
        if type(self) is type(other):
            return (
                self.fixing_commit == other.fixing_commit and
                self.introducing_commits == other.introducing_commits and
                self.issue_id == other.issue_id
            )
        return False

    def __hash__(self) -> int:
        return hash(
            (self.fixing_commit, self.introducing_commits, self.issue_id)
        )


class RawBug:
    """Bug representation using the Commit Hashes as Strings."""

    def __init__(
        self, fixing_commit: str, introducing_commits: tp.List[str],
        issue_id: tp.Optional[int]
    ) -> None:
        self.__fixing_commit = fixing_commit
        self.__introducing_commits = introducing_commits
        self.__issue_id = issue_id

    @property
    def fixing_commit(self) -> str:
        """Hash of the commit fixing the bug as string."""
        return self.__fixing_commit

    @property
    def introducing_commits(self) -> tp.List[str]:
        """Hashes of the commits introducing the bug as List of strings."""
        return self.__introducing_commits

    @property
    def issue_id(self) -> tp.Optional[int]:
        """ID of the issue associated with the bug, if there is one."""
        return self.__issue_id

    def __eq__(self, other) -> bool:
        if type(self) is type(other):
            return (
                self.fixing_commit == other.fixing_commit and
                self.introducing_commits == other.introducing_commits and
                self.issue_id == other.issue_id
            )
        return False

    def __hash__(self) -> int:
        return hash(
            (self.fixing_commit, self.introducing_commits, self.issue_id)
        )


def _has_closed_a_bug(issue_event: IssueEvent) -> bool:
    """
    Determines for a given issue event whether it closes an issue representing a
    bug or not.

    Args:
        issue_event: the issue event to be checked

    Returns:
        true if the issue represents a bug and the issue event closed that issue
        false ow.
    """
    if issue_event.event != "closed" or issue_event.commit_id is None:
        return False
    for label in issue_event.issue.labels:
        if label.name == "bug":
            return True
    return False


def _is_closing_message(commit_message: str) -> bool:
    """
    Determines for a given commit message whether it indicates that a bug has
    been closed by the corresponding commit.

    Args:
        commit_message: the commit message to be checked

    Returns:
        true if the commit message contains key words that indicate the
        closing of a bug, false ow.
    """
    # only look for keyword in first line of commit message
    first_line = commit_message[0:commit_message.index('\n')]

    match = re.search(r'fix|fixed|fixes', first_line, re.IGNORECASE)
    if match:  # None if re.search did not find a match
        return True
    return False


def _get_all_issue_events(project_name: str) -> tp.List[IssueEvent]:
    """
    Loads and returns all issue events for a given project.

    Args:
        project_name: The name of the project to look in.

    Returns:
        A list of IssueEvent objects or None.
    """

    def load_issue_events(github: Github) -> PaginatedList[IssueEvent]:
        repository: Repository = github.get_repo(project_name)
        return repository.get_issues_events()

    repo_path = get_local_project_git_path(project_name)
    cache_file_name = repo_path.name.replace("/", "_") + "_issues_events"

    issue_events = get_cached_github_object_list(
        cache_file_name, load_issue_events
    )

    if issue_events:
        return issue_events
    return []


def _search_corresponding_pygit_bug(
    closing_commit: str,
    project_repo: pygit2.Repository,
    issue_number: tp.Optional[int] = None
) -> PygitBug:
    """
    Returns the PygitBug corresponding to a given closing commit.

    Args:
        closing_commit: ID of the commit closing the bug.
        project_repo: The related pygit2 project Repository
        issue_number: The bug's issue number if there is an issue
            related to the bug.

    Returns:
        A PygitBug Object or None.
    """

    closing_pycommit: pygit2.Commit = project_repo.revparse_single(
        closing_commit
    )

    introducing_pycommits: tp.List[pygit2.Commit] = []
    # TODO find introducing commits

    return PygitBug(closing_pycommit, introducing_pycommits, issue_number)


def _search_corresponding_raw_bug(
    closing_commit: str,
    project_repo: pygit2.Repository,
    issue_number: tp.Optional[int] = None
) -> RawBug:
    """
    Returns the RawBug corresponding to a given closing commit.

    Args:
        closing_commit: ID of the commit closing the bug.
        project_repo: The related pygit2 project Repository
        issue_number: The bug's issue number if there is an issue
            related to the bug.

    Returns:
        A RawBug Object or None.
    """

    introducing_ids: tp.List[str] = []

    # TODO find introducing commits

    return RawBug(closing_commit, introducing_ids, issue_number)


def _filter_all_pygit_bugs(
    project_name: str,
    issue_filter_function: tp.Callable[[IssueEvent], tp.Optional[PygitBug]],
    commit_filter_function: tp.Callable[[pygit2.Commit], tp.Optional[PygitBug]]
) -> tp.FrozenSet[PygitBug]:
    """
    Wrapper function that uses given functions to filter out a certain type of
    PygitBugs using both issue events and the commit history.

    Args:
        project_name: Name of the project to draw the issue events and
            commit history out of.
        issue_filter_function: Function that determines for an issue event
            whether it produces an acceptable PygitBug or not.
        commit_filter_function: Function that determines for a commit
            whether it produces an acceptable PygitBug or not.

    Returns:
        The set of PygitBugs accepted by the filtering methods.
    """
    resulting_pygit_bugs = set()

    # iterate over all issue events
    issue_events = _get_all_issue_events(project_name)
    for issue_event in issue_events:
        pybug = issue_filter_function(issue_event)
        if pybug:
            resulting_pygit_bugs.add(pybug)

    project_repo = get_local_project_git(project_name)
    # traverse commit history
    most_recent_commit = project_repo[project_repo.head.target]
    for commit in project_repo.walk(
        most_recent_commit.id, pygit2.GIT_SORT_TIME
    ):
        pybug = commit_filter_function(commit)
        if pybug:
            resulting_pygit_bugs.add(pybug)

    return frozenset(resulting_pygit_bugs)


def _filter_all_raw_bugs(
    project_name: str, issue_filter_function: tp.Callable[[IssueEvent],
                                                          tp.Optional[RawBug]],
    commit_filter_function: tp.Callable[[pygit2.Commit], tp.Optional[RawBug]]
) -> tp.FrozenSet[RawBug]:
    """
    Wrapper function that uses given function to filter out a certain type of
    RawBugs using both issue events and the commit history.

    Args:
        project_name: Name of the project to draw the issue events and
            commit history out of.
        issue_filter_function: Function that determines for an issue event
            whether it produces an acceptable RawBug or not.
        commit_filter_function: Function that determines for a commit
            whether it produces an acceptable RawBug or not.

    Returns:
        The set of RawBugs accepted by the filtering methods.
    """
    resulting_raw_bugs = set()

    # iterate over all issue events
    issue_events = _get_all_issue_events(project_name)
    for issue_event in issue_events:
        rawbug = issue_filter_function(issue_event)
        if rawbug:
            resulting_raw_bugs.add(rawbug)

    project_repo = get_local_project_git(project_name)
    # traverse commit history
    most_recent_commit = project_repo[project_repo.head.target]
    for commit in project_repo.walk(
        most_recent_commit.id, pygit2.GIT_SORT_TIME
    ):
        rawbug = commit_filter_function(commit)
        if rawbug:
            resulting_raw_bugs.add(rawbug)

    return frozenset(resulting_raw_bugs)


def find_all_pygit_bugs(project_name: str) -> tp.FrozenSet[PygitBug]:
    """
    Creates a set of all bugs.

    Args:
        project_name: Name of the project in which to search for bugs

    Returns:
        A set of PygitBugs.
    """

    def accept_all_issue_pybugs(
        issue_event: IssueEvent
    ) -> tp.Optional[PygitBug]:
        if _has_closed_a_bug(issue_event) and issue_event.commit_id:
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            return _search_corresponding_pygit_bug(
                issue_event.commit_id, pygit_repo, issue_event.issue.number
            )
        return None

    def accept_all_commit_pybugs(
        commit: pygit2.Commit
    ) -> tp.Optional[PygitBug]:
        if _is_closing_message(commit.message):
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            return _search_corresponding_pygit_bug(commit.hex, pygit_repo)
        return None

    return _filter_all_pygit_bugs(
        project_name, accept_all_issue_pybugs, accept_all_commit_pybugs
    )


def find_all_raw_bugs(project_name: str) -> tp.FrozenSet[RawBug]:
    """
    Creates a set of all bugs.

    Args:
        project_name: Name of the project in which to search for bugs

    Returns:
        A set of RawBugs.
    """

    def accept_all_issue_rawbugs(
        issue_event: IssueEvent
    ) -> tp.Optional[RawBug]:
        if _has_closed_a_bug(issue_event) and issue_event.commit_id:
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            return _search_corresponding_raw_bug(
                issue_event.commit_id, pygit_repo, issue_event.issue.number
            )
        return None

    def accept_all_commit_rawbugs(commit: pygit2.Commit) -> tp.Optional[RawBug]:
        if _is_closing_message(commit.message):
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            return _search_corresponding_raw_bug(commit.hex, pygit_repo)
        return None

    return _filter_all_raw_bugs(
        project_name, accept_all_issue_rawbugs, accept_all_commit_rawbugs
    )


def find_pygit_bug_by_fix(project_name: str,
                          fixing_commit: str) -> tp.FrozenSet[PygitBug]:
    """
    Find the bug associated to some fixing commit, if there is any.

    Args:
        project_name: Name of the project in which to search for bugs
        fixing_commit: Commit Hash of the potentially fixing commit

    Returns:
        A set of PygitBugs fixed by fixing_commit
    """

    def accept_issue_pybug_with_certain_fix(
        issue_event: IssueEvent
    ) -> tp.Optional[PygitBug]:
        if _has_closed_a_bug(issue_event) and issue_event.commit_id:
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            pybug = _search_corresponding_pygit_bug(
                issue_event.commit_id, pygit_repo, issue_event.issue.number
            )
            if pybug.fixing_commit.hex == fixing_commit:
                return pybug
        return None

    def accept_commit_pybug_with_certain_fix(
        commit: pygit2.Commit
    ) -> tp.Optional[PygitBug]:
        if _is_closing_message(commit.message):
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            pybug = _search_corresponding_pygit_bug(commit.hex, pygit_repo)
            if pybug.fixing_commit.hex == fixing_commit:
                return pybug
        return None

    return _filter_all_pygit_bugs(
        project_name, accept_issue_pybug_with_certain_fix,
        accept_commit_pybug_with_certain_fix
    )


def find_raw_bug_by_fix(project_name: str,
                        fixing_commit: str) -> tp.FrozenSet[RawBug]:
    """
    Find the bug associated to some fixing commit, if there is any.

    Args:
        project_name: Name of the project in which to search for bugs
        fixing_commit: Commit Hash of the potentially fixing commit

    Returns:
        A set of RawBugs fixed by fixing_commit
    """

    def accept_issue_rawbug_with_certain_fix(
        issue_event: IssueEvent
    ) -> tp.Optional[RawBug]:
        if _has_closed_a_bug(issue_event) and issue_event.commit_id:
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            rawbug = _search_corresponding_raw_bug(
                issue_event.commit_id, pygit_repo, issue_event.issue.number
            )
            if rawbug.fixing_commit == fixing_commit:
                return rawbug
        return None

    def accept_commit_rawbug_with_certain_fix(
        commit: pygit2.Commit
    ) -> tp.Optional[RawBug]:
        if _is_closing_message(commit.message):
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            rawbug = _search_corresponding_raw_bug(commit.hex, pygit_repo)
            if rawbug.fixing_commit == fixing_commit:
                return rawbug
        return None

    return _filter_all_raw_bugs(
        project_name, accept_issue_rawbug_with_certain_fix,
        accept_commit_rawbug_with_certain_fix
    )


def find_pygit_bug_by_introduction(
    project_name: str, introducing_commit: str
) -> tp.FrozenSet[PygitBug]:
    """
    Create a (potentially empty) list of bugs introduced by a certain commit.

    Args:
        project_name: Name of the project in which to search for bugs
        introducing_commit: Commit Hash of the introducing commit to look for

    Returns:
        A set of PygitBugs introduced by introducing_commit
    """

    def accept_issue_pybug_with_certain_introduction(
        issue_event: IssueEvent
    ) -> tp.Optional[PygitBug]:
        if _has_closed_a_bug(issue_event) and issue_event.commit_id:
            pygit_repo = get_local_project_git(project_name)
            pybug = _search_corresponding_pygit_bug(
                issue_event.commit_id, pygit_repo, issue_event.issue.number
            )

            for introducing_pycommit in pybug.introducing_commits:
                if introducing_pycommit.hex == introducing_commit:
                    return pybug
                    # found wanted ID
        return None

    def accept_commit_pybug_with_certain_introduction(
        commit: pygit2.Commit
    ) -> tp.Optional[PygitBug]:
        if _is_closing_message(commit.message):
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            pybug = _search_corresponding_pygit_bug(commit.hex, pygit_repo)

            for introducing_pycommit in pybug.introducing_commits:
                if introducing_pycommit == introducing_commit:
                    return pybug
        return None

    return _filter_all_pygit_bugs(
        project_name, accept_issue_pybug_with_certain_introduction,
        accept_commit_pybug_with_certain_introduction
    )


def find_raw_bug_by_introduction(
    project_name: str, introducing_commit: str
) -> tp.FrozenSet[RawBug]:
    """
    Create a (potentially empty) list of bugs introduced by a certain commit.

    Args:
        project_name: Name of the project in which to search for bugs
        introducing_commit: Commit Hash of the introducing commit to look for

    Returns:
        A set of RawBugs introduced by introducing_commit
    """

    def accept_issue_rawbug_with_certain_introduction(
        issue_event: IssueEvent
    ) -> tp.Optional[RawBug]:
        if _has_closed_a_bug(issue_event) and issue_event.commit_id:
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            rawbug = _search_corresponding_raw_bug(
                issue_event.commit_id, pygit_repo, issue_event.issue.number
            )

            for introducing_id in rawbug.introducing_commits:
                if introducing_id == introducing_commit:
                    return rawbug
                    # found wanted ID
        return None

    def accept_commit_rawbug_with_certain_introduction(
        commit: pygit2.Commit
    ) -> tp.Optional[RawBug]:
        if _is_closing_message(commit.message):
            pygit_repo: pygit2.Repository = get_local_project_git(project_name)
            rawbug = _search_corresponding_raw_bug(commit.hex, pygit_repo)

            for introducing_pycommit in rawbug.introducing_commits:
                if introducing_pycommit == introducing_commit:
                    return rawbug
        return None

    return _filter_all_raw_bugs(
        project_name, accept_issue_rawbug_with_certain_introduction,
        accept_commit_rawbug_with_certain_introduction
    )
