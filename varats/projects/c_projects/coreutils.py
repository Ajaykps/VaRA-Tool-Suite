"""Project file for the GNU coreutils."""
import typing as tp
from pathlib import Path

import benchbuild as bb
from benchbuild.utils.cmd import git, make
from benchbuild.utils.settings import get_number_of_jobs
from plumbum import local

from varats.data.provider.cve.cve_provider import CVEProviderHook
from varats.paper.paper_config import project_filter_generator
from varats.settings import bb_cfg
from varats.utils.project_util import (
    wrap_paths_to_binaries,
    ProjectBinaryWrapper,
)


class Coreutils(bb.Project, CVEProviderHook):  # type: ignore
    """GNU coretuils / UNIX command-line tools (fetched by Git)"""

    NAME = 'coreutils'
    GROUP = 'c_projects'
    DOMAIN = 'utils'

    SOURCE = [
        bb.source.Git(
            remote="https://github.com/coreutils/coreutils.git",
            local="coreutils",
            refspec="HEAD",
            limit=None,
            shallow=False,
            version_filter=project_filter_generator("coreutils")
        )
    ]

    @property
    def binaries(self) -> tp.List[ProjectBinaryWrapper]:
        """Return a list of binaries generated by the project."""
        return wrap_paths_to_binaries([
            # figure out how to handle this file correctly in filenames
            # 'src/[',
            'src/uniq',
            'src/dircolors',
            'src/numfmt',
            'src/b2sum',
            'src/mv',
            'src/fold',
            'src/dir',
            'src/mkfifo',
            'src/vdir',
            'src/sha512sum',
            'src/unexpand',
            'src/join',
            'src/nproc',
            'src/ptx',
            'src/printf',
            'src/ginstall',
            'src/du',
            'src/printenv',
            # 'dcgen', was not found in version #961d668
            'src/groups',
            'src/sync',
            'src/ln',
            'src/shuf',
            'src/false',
            'src/mkdir',
            'src/chmod',
            'src/link',
            'src/cat',
            'src/pwd',
            'src/chown',
            'src/head',
            'src/sleep',
            'src/fmt',
            'src/getlimits',
            'src/test',
            'src/paste',
            'src/comm',
            'src/mknod',
            'src/kill',
            'src/sha384sum',
            'src/sort',
            'src/sum',
            'src/sha224sum',
            'src/expand',
            'src/basenc',
            'src/truncate',
            'src/dd',
            'src/tail',
            'src/df',
            'src/tee',
            'src/tsort',
            'src/yes',
            'src/sha1sum',
            'src/rm',
            'src/make-prime-list',
            'src/logname',
            'src/pathchk',
            'src/whoami',
            'src/wc',
            'src/basename',
            'src/nohup',
            # 'libstdbuf.so', could not find in version #961d668
            'src/chroot',
            'src/users',
            'src/csplit',
            # 'stdbuf',  is no tool
            'src/hostid',
            'src/readlink',
            'src/timeout',
            'src/base64',
            'src/id',
            'src/nl',
            'src/stat',
            'src/cp',
            'src/shred',
            'src/who',
            'src/tr',
            'src/echo',
            'src/date',
            'src/split',
            'src/seq',
            'src/md5sum',
            'src/env',
            'src/expr',
            'src/true',
            'src/chcon',
            'src/chgrp',
            'src/mktemp',
            'src/unlink',
            'src/uname',
            'src/pinky',
            'src/stty',
            'src/rmdir',
            'src/ls',
            'src/runcon',
            'src/nice',
            # 'blake2', is a folder
            'src/tty',
            'src/factor',
            'src/tac',
            'src/realpath',
            'src/pr',
            'src/sha256sum',
            # 'du-tests', removed due to bash script
            'src/cksum',
            'src/touch',
            'src/cut',
            'src/od',
            'src/base32',
            'src/uptime',
            'src/dirname',
        ])

    def run_tests(self) -> None:
        coreutils_source = bb.path(self.source_of(self.primary_source))
        with local.cwd(coreutils_source):
            bb.watch(make)("-j", get_number_of_jobs(bb_cfg()), "check")

    def compile(self) -> None:
        coreutils_source = bb.path(self.source_of(self.primary_source))
        compiler = bb.compiler.cc(self)
        with local.cwd(coreutils_source):
            git("submodule", "init")
            git("submodule", "update")
            with local.env(CC=str(compiler)):
                bb.watch(local["./bootstrap"])()
                bb.watch(local["./configure"])("--disable-gcc-warnings")

            bb.watch(make)("-j", get_number_of_jobs(bb_cfg()))
            for binary in self.binaries:
                if not Path("{binary}".format(binary=binary)).exists():
                    print("Could not find {binary}")

    @classmethod
    def get_cve_product_info(cls) -> tp.List[tp.Tuple[str, str]]:
        return [("gnu", "coreutils")]
