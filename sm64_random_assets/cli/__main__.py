#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import sys
import ubelt as ub


def main(cmdline=True, **kw):
    """
    kw = dict(command='stats')
    cmdline = False
    """
    modnames = [
        'generate',
        'grab_baserom',
    ]
    module_lut = {}
    for name in modnames:
        mod = ub.import_module_from_name('sm64_random_assets.cli.{}'.format(name))
        module_lut[name] = mod

    # Create a list of all submodules with CLI interfaces
    cli_modules = list(module_lut.values())

    # Create a subparser that uses the first positional argument to run one of
    # the previous CLI interfaces.
    from scriptconfig.modal import ModalCLI
    modal = ModalCLI(description=ub.codeblock(
        '''
        The SM64 Random Assets CLI
        '''))

    def get_version(self):
        import sm64_random_assets
        return sm64_random_assets.__version__
    modal.__class__.version = property(get_version)

    for cli_module in cli_modules:

        cli_config = None
        if hasattr(cli_module, '__cli__'):
            # New way
            cli_config = cli_module.__cli__
        else:
            raise NotImplementedError(f'modules must define the __cli__ attribute to be registered. Failed on {cli_module}')

        # Update configs to have aliases / commands attributes
        # cli_modname = cli_module.__name__
        # cli_rel_modname = cli_modname.split('.')[-1]
        cmdname_aliases = ub.oset()
        alias = getattr(cli_module, '__alias__', getattr(cli_config, '__alias__', []))
        if isinstance(alias, str):
            alias = [alias]
        command = getattr(cli_module, '__command__', getattr(cli_config, '__command__', None))
        if command is not None:
            cmdname_aliases.add(command)
        cmdname_aliases.update(alias)
        # cmdname_aliases.update(cmd_alias.get(cli_modname, []) )
        cmdname_aliases.add(cli_config.__command__)
        primary_cmdname = cmdname_aliases[0]
        secondary_cmdnames = cmdname_aliases[1:]
        cli_config.__command__ = primary_cmdname
        cli_config.__alias__ = secondary_cmdnames
        modal.register(cli_config)

    ret = modal.run(strict=True)
    return ret


if __name__ == '__main__':
    sys.exit(main())
