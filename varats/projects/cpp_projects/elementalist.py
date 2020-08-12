"""Project file for TODO: ."""
import typing as tp

from benchbuild.project import Project
from benchbuild.utils.cmd import cmake, git, make
from benchbuild.utils.compiler import cc
from benchbuild.utils.download import with_git
from benchbuild.utils.run import run
from benchbuild.utils.settings import get_number_of_jobs
from plumbum import local

from varats.data.provider.cve.cve_provider import CVEProviderHook
from varats.paper.paper_config import project_filter_generator
from varats.settings import bb_cfg
from varats.utils.project_util import (
    BlockedRevision,
    BlockedRevisionRange,
    ProjectBinaryWrapper,
    BugAndFixPair,
    block_revisions,
    get_all_revisions_between,
    wrap_paths_to_binaries,
)


@block_revisions([])
@with_git(
    "",  #TODO:
    refspec="HEAD",
    shallow_clone=False,
    version_filter=project_filter_generator("")  #TODO
)
class Gravity(Project, CVEProviderHook):  # type: ignore
    """Programming language TODO: ."""

    NAME = ''  #TODO:
    GROUP = 'cpp_projects'
    DOMAIN = 'UNIX utils'
    VERSION = 'HEAD'

    SRC_FILE = NAME + "-{0}".format(VERSION)

    @property
    def binaries(self) -> tp.List[ProjectBinaryWrapper]:
        """Return a list of binaries generated by the project."""
        return wrap_paths_to_binaries([""])  #TODO:

    def run_tests(self, runner: run) -> None:
        pass

    def compile(self) -> None:
        self.download()

        # cmake as build system
        with local.cwd(self.SRC_FILE):
            version_id = git("rev-parse", "HEAD").strip()
            cmake_revisions = get_all_revisions_between(
                "dbb4d61fc2ebb9aca44e8e6bb978efac4a6def87", "master"
            )  #TODO:

        if version_id in cmake_revisions:
            self.__compile_cmake()
        else:
            self.__compile_make()

    def __compile_cmake(self) -> None:
        clang = cc(self)
        with local.cwd(self.SRC_FILE):
            with local.env(CC=str(clang)):
                cmake("-G", "Unix Makefiles", ".")
            run(make["-j", get_number_of_jobs(bb_cfg())])

    def __compile_make(self) -> None:
        clang = cc(self)
        with local.cwd(self.SRC_FILE):
            with local.env(CC=str(clang)):
                run(make["-j", get_number_of_jobs(bb_cfg())])

    @classmethod
    def get_cve_product_info(cls) -> tp.List[tp.Tuple[str, str]]:
        return [("", "")]  #TODO: