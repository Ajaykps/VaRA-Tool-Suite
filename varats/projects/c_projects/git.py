"""Project file for git."""
import typing as tp

import benchbuild as bb
from benchbuild.utils.cmd import make
from benchbuild.utils.settings import get_number_of_jobs
from plumbum import local
from plumbum.path.utils import delete

from varats.data.provider.cve.cve_provider import CVEProviderHook
from varats.paper.paper_config import project_filter_generator
from varats.settings import bb_cfg
from varats.utils.project_util import (
    wrap_paths_to_binaries,
    ProjectBinaryWrapper,
)


class Git(bb.Project, CVEProviderHook):  # type: ignore
    """Git."""

    NAME = 'git'
    GROUP = 'c_projects'
    DOMAIN = 'version control'

    SOURCE = [
        bb.source.Git(
            remote="https://github.com/git/git.git",
            local="git",
            refspec="HEAD",
            limit=None,
            shallow=False,
            # version_filter=project_filter_generator("git")
        )
    ]

    @property
    def binaries(self) -> tp.List[ProjectBinaryWrapper]:
        """Return a list of binaries generated by the project."""
        return wrap_paths_to_binaries(["git"])

    def run_tests(self) -> None:
        pass

    def compile(self) -> None:
        git_source = bb.path(self.source_of(self.primary_source))

        clang = bb.compiler.cc(self)
        with local.cwd(git_source):
            with local.env(CC=str(clang)):
                delete("configure", "config.status")
                bb.watch(make)("configure")
                bb.watch(local["./configure"])()
            bb.watch(make)("-j", get_number_of_jobs(bb_cfg()))

    @classmethod
    def get_cve_product_info(cls) -> tp.List[tp.Tuple[str, str]]:
        return [("git", "git")]
