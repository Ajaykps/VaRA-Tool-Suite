"""Project file for qemu."""
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


class Qemu(bb.Project, CVEProviderHook):  # type: ignore
    """
    QEMU, the FAST!

    processor emulator.
    """

    NAME = 'qemu'
    GROUP = 'c_projects'
    DOMAIN = 'Hardware emulator'

    SOURCE = [
        bb.source.Git(
            remote="https://github.com/qemu/qemu.git",
            local="qemu",
            refspec="HEAD",
            limit=None,
            shallow=False,
            # version_filter=project_filter_generator("qemu")
        )
    ]

    @property
    def binaries(self) -> tp.List[ProjectBinaryWrapper]:
        """Return a list of binaries generated by the project."""
        return wrap_paths_to_binaries([
            "build/x86_64-softmmu/qemu-system-x86_64"
        ])

    def run_tests(self) -> None:
        pass

    def compile(self) -> None:
        qemu_source = bb.path(self.source_of(self.primary_source))

        self.cflags += ['-Wno-tautological-type-limit-compare']

        c_compiler = bb.compiler.cc(self)
        cxx_compiler = bb.compiler.cxx(self)
        build_folder = qemu_source / "build"
        build_folder.mkdir()

        with local.cwd(build_folder):
            with local.env(CC=str(c_compiler), CXX=str(cxx_compiler)):
                configure = bb.watch(local["../configure"])
                configure(
                    "--disable-debug-info", "--target-list=x86_64-softmmu"
                )
                bb.watch(make)("-j", get_number_of_jobs(bb_cfg()))

    @classmethod
    def get_cve_product_info(cls) -> tp.List[tp.Tuple[str, str]]:
        return [("qemu", "qemu")]
