#!/usr/bin/env python3
import scriptconfig as scfg
import ubelt as ub


class GrabBaseromCLI(scfg.DataConfig):
    """
    Convinience tool to copy the baserom into the current path.

    Requires that you have a copy of the baserom.us.z64 in a known locations.
    """
    __command__ = 'grab_baserom'

    dst = scfg.Value('.', help='directory or file path to copy the baserom to', position=1)

    @classmethod
    def main(cls, cmdline=1, **kwargs):
        import rich
        from rich.markup import escape
        config = cls.cli(cmdline=cmdline, data=kwargs, strict=True)
        rich.print('config = ' + escape(ub.urepr(config, nl=1)))

        try:
            mod_dpath = ub.Path(__file__).parent.parent
        except NameError:
            mod_dpath = ub.Path('~/code/sm64-random-assets/sm64_random_assets/').expand()
            assert mod_dpath.exists(), 'dev fallback failed'

        repo_dpath = mod_dpath.parent
        src_fpath = find_baserom_fpath(repo_dpath)
        print(f'Found baserom path: {src_fpath}')

        dst = ub.Path(config.dst)
        if dst.is_dir():
            dst_fpath = dst / 'baserom.us.z64'
        else:
            dst_fpath = dst

        if not dst_fpath.parent.exists():
            raise IOError('parent dir does not exist')

        if dst_fpath.exists():
            print('dst already exists, doing nothing')
        else:
            print('copy to:')
            print(f'dst_fpath={dst_fpath}')
            src_fpath.copy(dst_fpath)


def find_baserom_fpath(repo_dpath):
    candidates = [
        repo_dpath / 'baserom.us.z64'
    ]
    src_fpath = None
    for fpath in candidates:
        if fpath.exists():
            src_fpath = fpath
            break

    if src_fpath is None:
        if ub.find_exe('ipfs'):
            grab_from_secret_ipfs()
        else:
            print('IPFS is not installed, cannot use that method')

    if not src_fpath:
        raise FileNotFoundError('Cannot find baserom')

    # TODO: check the hash
    return src_fpath


def grab_from_secret_ipfs():
    # TODO: control target location better
    script_dpath = ub.Path.appdir('sm64_random_assets/scripts').ensuredir()
    bash_text = ub.codeblock(
        '''
        #!/bin/bash
        ROM_FPATH=${ROM_FPATH:=baserom.us.z64}
        if type -P secret_loader.sh; then
            # Developer testing with known secret path to a personal copy of the ROM
            # shellcheck disable=SC1090
            source "$(secret_loader.sh)"
            SM64_CID=$(load_secret_var sm64_us_cid)
            echo "SM64_CID = $SM64_CID"
            ipfs get "$SM64_CID" -o "$ROM_FPATH"
            echo "Grabbed $ROM_FPATH"
        else
            echo "
            !!!!!!!
            ERROR: This script is intended for internal development!
            It is a placeholder for some method to obtain a copy of a ROM.
            "
        fi
        ''')
    script_fpath = script_dpath / 'grab_reference_baserom_ipfs.sh'
    script_fpath.write_text(bash_text)
    ub.cmd(f'bash {script_fpath}', verbose=3)


__cli__ = GrabBaseromCLI

if __name__ == '__main__':
    """

    CommandLine:
        python ~/code/sm64-random-assets/sm64_random_assets/cli/grab_baserom.py
        python -m sm64_random_assets.cli.grab_baserom
    """
    __cli__.main()
