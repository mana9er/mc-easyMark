from .easyMark import EasyMarker

instance = None


def load(logger, core):
    # Function "load" is required by mana9er-core.
    from os import path
    save_file = path.join(core.init_cwd, 'easyMark', 'easyMark-saves.json')
    instance = EasyMarker(logger, core, save_file)
