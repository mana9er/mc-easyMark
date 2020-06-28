from .easyMark import EasyMarker


def load(logger, core):
    # Function "load" is required by mana9er-core.
    from os import path
    config_file = path.join(core.root_dir, 'easyMark', 'config.json')
    save_file = path.join(core.root_dir, 'easyMark', 'easyMark-saves.json')
    EasyMarker(logger, core, config_file, save_file)
