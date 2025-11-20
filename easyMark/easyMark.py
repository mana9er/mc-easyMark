from PyQt5 import QtCore
import os
import json
import time

from . import parser

__all__ = ['EasyMarker']


class EasyMarker(QtCore.QObject):
    cmd_prefix = '!mark'

    def __init__(self, logger, core, config_file, saved_file):
        super(EasyMarker, self).__init__(core)
        self.logger = logger
        self.saved_file = saved_file
        self.disabled = False

        # load config
        self.configs = {}
        if os.path.exists(config_file):
            self.logger.info('Loading configs...')
            with open(config_file, 'r', encoding='utf-8') as cf:
                self.configs = json.load(cf)
        else:
            self.logger.warning('config.json not found. Using default settings.')

        # load previous saved marks
        if os.path.exists(self.saved_file):
            self.logger.info('Loading saved marks...')
            with open(self.saved_file, 'r', encoding='utf-8') as sf:
                self.marks = json.load(sf)
        else:
            self.logger.warning('Failed to find previous saved marks')
            self.logger.info('Creating new marks...')
            self.marks = {'.public': {}}
            json.dump(self.marks, open(self.saved_file, 'w', encoding='utf-8'), indent=2)

        # load mcBasicLib
        self.utils = core.get_plugin('mcBasicLib')
        if self.utils is None:
            self.logger.error('Failed to load plugin "mcBasicLib", easyMark will be disabled.')
            self.logger.error('Please make sure that "mcBasicLib" has been added to plugins.')
            self.disabled = True

        if self.disabled:
            return
        
        # connect signals and slots
        self.utils.sig_input.connect(self.on_player_input)

        # available commands
        self.cmd_list = {
            'help': self.help,
            'list': self.list_marks,
            'add': self.add_marks,
            'rm': self.rm_marks,
            'show': self.show_marks,
            'search': self.search_marks,
        }

    def unknown_command(self, player):
        self.logger.warning('Unknown command typed by player {}.'.format(player.name))
        self.utils.tell(player, 'Unknown command. Type "!mark help" for help.')

    @QtCore.pyqtSlot(tuple)
    def on_player_input(self, pair):
        self.logger.debug('EasyMarker.on_player_input called')
        player, text = pair
        text_list = parser.split_text(text)
        
        if len(text_list) == 0:
            return
        
        if text_list[0] == self.cmd_prefix:
            if len(text_list) > 1 and text_list[1] in self.cmd_list.keys():
                self.cmd_list[text_list[1]](player, text_list)
            else:
                self.unknown_command(player)

    def help(self, player, text_list):
        self.logger.debug('EasyMarker.help called')
        self.utils.tell(player, 'Welcome to easyMark!')
        self.utils.tell(player, 'You are able to use the following commands:')
        self.utils.tell(player, '"!mark help": show this help message.')
        self.utils.tell(player, '"!mark list [public | private]": list out all the marks. Use argument "public" or "private" to see public or private marks only.')
        self.utils.tell(player, '"!mark add [public] <name> <content>": add a mark. Use argument "public" to make it visible to all players.')
        self.utils.tell(player, '"!mark rm <name>": remove a mark.')
        self.utils.tell(player, '"!mark show <name>": show details of the mark.')
        self.utils.tell(player, '"!mark search <text>": search marks containing the given text.')

    def list_marks(self, player, text_list):
        self.logger.debug('EasyMarker.list_marks called')
        public, private = True, True
        if len(text_list) == 2:
            pass
        elif len(text_list) == 3:
            if text_list[2] == 'public':
                private = False
            elif text_list[2] == 'private':
                public = False
            else:
                self.unknown_command(player)
                return
        else:
            self.unknown_command(player)
            return

        if public:
            self.utils.tell(player, 'Public marks:')
            if len(self.marks['.public']) > 0:
                for mark in self.marks['.public'].values():     # mark: dict
                    self._tell_clickable_mark(player, mark)
            else:
                self.utils.tell(player, 'No public mark yet.')
        if private:
            self.utils.tell(player, 'Private marks:')
            if player.name in self.marks and len(self.marks[player.name]) > 0:
                for mark in self.marks[player.name].values():   # mark: dict
                    self._tell_clickable_mark(player, mark)
            else:
                self.utils.tell(player, 'No private mark yet.')

    def add_marks(self, player, text_list):
        self.logger.debug('EasyMarker.add_marks called')
        public = False
        if text_list[2] == 'public':
            if len(text_list) >= 5:
                # parse the last text groups as content
                name, content = text_list[3], parser.join_text_list(text_list[4:])
                
                p_p_l = 'op'  # default setting is 'op'
                if 'public_permission_level' in self.configs:
                    p_p_l = self.configs['public_permission_level']
                
                if p_p_l == 'op':
                    if player.is_op():
                        public = True
                    else:
                        self.utils.tell(player, 'Only op can make public marks. Permission denied.')
                        return
                else:
                    public = True
                    if p_p_l != 'any':
                        self.logger.warning('Unacceptable keyword for "public_permission_level" in config.json')
                        self.utils.tell(player, 'Permission denied. Unacceptable config settings.')
                        return

            else:
                self.utils.tell(player, 'Missing argument <content>.')
                return
        elif len(text_list) >= 4:
            # parse the last text groups as content
            name, content = text_list[2], parser.join_text_list(text_list[3:])
        else:
            self.unknown_command(player)
            return

        if name in self.marks['.public'] or name in self.marks.get(player.name, {}):
            self.utils.tell(player, 'This mark has already existed. Remove that mark first or use another name.')
            return
        new_mark = {
            'name': name,
            'content': content,
            'player': player.name,
            'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            'public': public
        }

        info = ' mark "{}" has been successfully saved.'.format(name)
        if public:
            self.marks['.public'][name] = new_mark
            info = 'Public' + info
        else:
            if player.name not in self.marks:
                self.marks[player.name] = {}
            self.marks[player.name][name] = new_mark
            info = 'Private' + info
        json.dump(self.marks, open(self.saved_file, 'w', encoding='utf-8'), indent=2)
        self.utils.tell(player, info)

    def rm_marks(self, player, text_list):
        self.logger.debug('EasyMarker.rm_marks called')
        if len(text_list) == 3:
            name = text_list[2]
            if player.name in self.marks and name in self.marks[player.name]:
                del self.marks[player.name][name]
                json.dump(self.marks, open(self.saved_file, 'w', encoding='utf-8'), indent=2)
                self.utils.tell(player, 'Private mark "{}" has been successfully deleted.'.format(name))
                return
            elif name in self.marks['.public']:
                if player.is_op():
                    del self.marks['.public'][name]
                    json.dump(self.marks, open(self.saved_file, 'w', encoding='utf-8'), indent=2)
                    self.utils.tell(player, 'Public mark "{}" has been successfully deleted.'.format(name))
                else:
                    self.utils.tell(player, 'Only op can remove public marks. Permission denied.')
                    return
            else:
                self.utils.tell(player, 'Cannot find this mark. Make sure the name is correct.')
                return
        else:
            self.unknown_command(player)

    def show_marks(self, player, text_list):
        self.logger.debug('EasyMarker.show_marks called')
        if len(text_list) == 3:
            mark_name = text_list[2]
            if player.name in self.marks and mark_name in self.marks[player.name]:
                mark = self.marks[player.name][mark_name]
            elif mark_name in self.marks['.public']:
                mark = self.marks['.public'][mark_name]
            else:
                self.utils.tell(player, 'Cannot find this mark. Make sure the name is correct.')
                return
            self.utils.tell(player, self._gen_detail_str(mark))
            self.utils.tell(player, mark['content'])
        else:
            self.unknown_command(player)

    def search_marks(self, player, text_list):
        self.logger.debug('EasyMarker.search_marks called')
        if len(text_list) == 3:
            text = text_list[2]
            # search public marks
            cnt = 0
            self.utils.tell(player, 'Public marks:')
            for name in self.marks['.public']:
                mark = self.marks['.public'][name]
                if text in mark['name'] or text in mark['content']:
                    cnt += 1
                    self.utils.tell(player, name)
            if cnt == 0:
                self.utils.tell(player, 'No public mark found.')
            # search private marks
            cnt = 0
            self.utils.tell(player, 'Private marks:')
            if player.name in self.marks:
                for name in self.marks[player.name]:
                    mark = self.marks[player.name][name]
                    if text in mark['name'] or text in mark['content']:
                        cnt += 1
                        self.utils.tell(player, name)
            if cnt == 0:
                self.utils.tell(player, 'No private mark found.')
        else:
            self.unknown_command(player)

    def _gen_detail_str(self, mark: dict) -> str:
        """ Generate the detail string for a mark. """
        detail_str = ' mark "{}" was marked by {} at {}'.format(mark['name'], mark['player'], mark['time'])
        detail_str = ('Public' if mark['public'] else 'Private') + detail_str
        return detail_str
    
    def _tell_clickable_mark(self, player, mark: dict):
        """ 
        `/tellraw` the `player` the specified `mark` with clickEvent and hoverEvent.         
        Keys required in the mark dict: `'name'`, `'content'`, `'player'`, `'time'`.
        """
        self.logger.debug('EasyMarker._tell_clickable_mark called')

        click_textcomp = [
            # the text component to show when the told mark is clicked
            # keep the same output format as in `show_marks()`
            {'text': self._gen_detail_str(mark), 'color': 'yellow'},
            {'text': '\n' + mark['content'], 'color': 'yellow'}
        ]
        hover_textcomp = [     # the text component to show when hovering over the told mark
            {'text': 'Marked by'},
            {'text': ' {}'.format(mark['player']), 'color': 'aqua'},
            {'text': ' at'},
            {'text': ' {}'.format(mark['time']), 'color': 'gold', 'italic': True},
            {'text': '\nClick to show mark content.', 'color': 'gray', 'italic': True},
        ]
        tell_textcomp = {
            'text': mark['name'],
            'color': 'aqua',
            'underlined': True,
            'hoverEvent': {
                'action': 'show_text',
                'value': hover_textcomp
            },
            'clickEvent': {
                'action': 'run_command',
                'value': '/tellraw @s {}'.format(json.dumps(click_textcomp))
            }
        }
        
        self.utils.tellraw(player, json.dumps(tell_textcomp))