"""Project file for FreeBSD."""
import typing as tp

from benchbuild.project import Project
from benchbuild.utils.cmd import make
from benchbuild.utils.compiler import cc
from benchbuild.utils.download import with_git
from benchbuild.utils.run import run
from benchbuild.utils.settings import get_number_of_jobs
from plumbum import local

from varats.data.provider.cve.cve_provider import CVEProviderHook
from varats.paper.paper_config import project_filter_generator
from varats.settings import bb_cfg
from varats.utils.project_util import (
    wrap_paths_to_binaries,
    ProjectBinaryWrapper,
)


@with_git(
    "https://github.com/freebsd/freebsd.git",
    refspec="HEAD",
    version_filter=project_filter_generator("FreeBSD")
)
class FreeBSD(Project, CVEProviderHook):  # type: ignore
    """The FreeBSD Project (fetched by Git)"""

    NAME = 'FreeBSD'
    GROUP = 'c_projects'
    DOMAIN = 'OS'
    VERSION = 'HEAD'

    SRC_FILE = NAME + "-{0}".format(VERSION)

    @property
    def binaries(self) -> tp.List[ProjectBinaryWrapper]:
        """Return a list of binaries generated by the project."""
        # TODO: What to input here?
        return wrap_paths_to_binaries(["FreeBSD"])

    def run_tests(self, runner: run) -> None:
        pass

    def compile(self) -> None:
        self.download()

        clang = cc(self)
        with local.cwd(self.SRC_FILE):
            # Hope, the kernel is enough to show OpenSSL behaviour; 'make universe' takes 167 GiB space...
            run(make["buildkernel", "-j", get_number_of_jobs(bb_cfg())])

    @classmethod
    def get_cve_product_info(cls) -> tp.List[tp.Tuple[str, str]]:
        return [("FreeBSD", "FreeBSD")]
