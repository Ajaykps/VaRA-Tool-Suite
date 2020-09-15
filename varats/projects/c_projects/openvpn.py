"""Project file for openvpn."""
import typing as tp

from benchbuild.project import Project
from benchbuild.utils.cmd import make, autoreconf, git
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
    "https://github.com/OpenVPN/openvpn.git",
    refspec="HEAD",
    version_filter=project_filter_generator("openvpn"),
    shallow_clone=False
)
class OpenVPN(Project, CVEProviderHook):  # type: ignore
    """OpenVPN is an open source VPN daemon (fetched by Git)"""

    NAME = 'openvpn'
    GROUP = 'c_projects'
    DOMAIN = 'security'
    VERSION = 'HEAD'

    SRC_FILE = NAME + "-{0}".format(VERSION)

    @property
    def binaries(self) -> tp.List[ProjectBinaryWrapper]:
        """Return a list of binaries generated by the project."""
        # What does this function do?
        return wrap_paths_to_binaries(["openvpn"])

    def run_tests(self, runner: run) -> None:
        pass

    def compile(self) -> None:
        self.download()

        clang = cc(self)
        with local.cwd(self.SRC_FILE):
            run(git["checkout", "release/2.5"])
            with local.env(CC=str(clang)):
                run(autoreconf["-i", "-v", "-f"])
                run(local["./configure"])
            run(make["-j", get_number_of_jobs(bb_cfg())])

    @classmethod
    def get_cve_product_info(cls) -> tp.List[tp.Tuple[str, str]]:
        return [("OpenVPN", "openvpn")]
