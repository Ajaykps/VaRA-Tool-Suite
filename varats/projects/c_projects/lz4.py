"""Project file for lz4."""
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


class Lz4(bb.Project, CVEProviderHook):  # type: ignore
    """
    LZ4 is lossless compression algorithm.

    (fetched by Git)
    """

    NAME = 'lz4'
    GROUP = 'c_projects'
    DOMAIN = 'compression'

    SOURCE = [
        bb.source.Git(
            remote="https://github.com/lz4/lz4.git",
            local="lz4",
            refspec="HEAD",
            limit=None,
            shallow=False,
            # version_filter=project_filter_generator("lz4")
        )
    ]

    @property
    def binaries(self) -> tp.List[ProjectBinaryWrapper]:
        """Return a list of binaries generated by the project."""
        return wrap_paths_to_binaries(['lz4'])

    def run_tests(self) -> None:
        pass

    def compile(self) -> None:
        lz4_source = bb.path(self.source_of(self.primary_source))

        clang = bb.compiler.cc(self)
        with local.cwd(lz4_source):
            with local.env(CC=str(clang)):
                bb.watch(make)("-j", get_number_of_jobs(bb_cfg()))

    @classmethod
    def get_cve_product_info(cls) -> tp.List[tp.Tuple[str, str]]:
        return [("Yann Collet", "LZ4")]
