"""Project file for curl."""
import typing as tp

import benchbuild as bb
from benchbuild.utils.cmd import make
from benchbuild.utils.settings import get_number_of_jobs
from plumbum import local

from varats.data.provider.cve.cve_provider import CVEProviderHook
from varats.paper.paper_config import project_filter_generator
from varats.settings import bb_cfg
from varats.utils.project_util import (
    wrap_paths_to_binaries,
    ProjectBinaryWrapper,
)


class Curl(bb.Project, CVEProviderHook):  # type: ignore
    """
    Curl is a command-line tool for transferring data specified with URL syntax.

    (fetched by Git)
    """

    NAME = 'curl'
    GROUP = 'c_projects'
    DOMAIN = 'web'

    SOURCE = [
        bb.source.Git(
            remote="https://github.com/curl/curl.git",
            local="curl",
            refspec="HEAD",
            limit=None,
            shallow=False,
            version_filter=project_filter_generator("curl")
        )
    ]

    @property
    def binaries(self) -> tp.List[ProjectBinaryWrapper]:
        """Return a list of binaries generated by the project."""
        return wrap_paths_to_binaries(['src/.libs/curl'])

    def run_tests(self) -> None:
        pass

    def compile(self) -> None:
        curl_source = bb.path(self.source_of(self.primary_source))

        clang = bb.compiler.cc(self)
        with local.cwd(curl_source):
            with local.env(CC=str(clang)):
                bb.watch(local["./buildconf"])()
                bb.watch(local["./configure"])()

            bb.watch(make)("-j", get_number_of_jobs(bb_cfg()))

    @classmethod
    def get_cve_product_info(cls) -> tp.List[tp.Tuple[str, str]]:
        return [("Haxx", "Curl")]
