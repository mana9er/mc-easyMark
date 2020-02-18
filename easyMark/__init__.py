from .easyMark import EasyMarker


def instance(logger, core):
    # Function "instance" is required by mana9er-core.
    from os import path
    save_file = path.join(core.init_cwd, 'easyMark', 'easyMark-saves.json')
    return EasyMarker(logger, core, save_file)
