"""Project file for busybox."""
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


class Busybox(bb.Project, CVEProviderHook):  # type: ignore
    """UNIX utility wrapper BusyBox."""

    NAME = 'busybox'
    GROUP = 'c_projects'
    DOMAIN = 'UNIX utils'

    SOURCE = [
        bb.source.Git(
            remote="https://github.com/mirror/busybox.git",
            local="busybox",
            refspec="HEAD",
            limit=None,
            shallow=False,
            # version_filter=project_filter_generator("busybox")
        )
    ]

    @property
    def binaries(self) -> tp.List[ProjectBinaryWrapper]:
        """Return a list of binaries generated by the project."""
        return wrap_paths_to_binaries(["PLEASE_REPLACE_ME"])

    def run_tests(self) -> None:
        pass

    def compile(self) -> None:
        busybox_source = bb.path(self.source_of(self.primary_source))

        clang = bb.compiler.cc(self)
        with local.cwd(busybox_source):
            with local.env(CC=str(clang)):
                bb.watch(make["defconfig"])()
                bb.watch(make)("-j", get_number_of_jobs(bb_cfg()))

    @classmethod
    def get_cve_product_info(cls) -> tp.List[tp.Tuple[str, str]]:
        return [("busybox", "busybox")]
