from .easyMark import EasyMarker


def load(logger, core):
    # Function "load" is required by mana9er-core.
    from os import path
    config_file = path.join(core.init_cwd, 'easyMark', 'config.json')
    save_file = path.join(core.init_cwd, 'easyMark', 'easyMark-saves.json')
    EasyMarker(logger, core, config_file, save_file)
