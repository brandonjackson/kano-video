import os
from gi.repository import Gtk

from kano.utils import list_dir

from .playlist import Playlist, add_to_playlist_handler
from .player import play_video, stop_videos
from .youtube import search_youtube_by_user, parse_youtube_entries, \
    search_youtube_by_keyword

from .general_ui import KanoWidget, Spacer


class VideoEntry(KanoWidget):
    _ENTRY_HEIGHT = 110
    _TITLE_HEIGHT = 20
    _DESC_HEIGHT = 15
    _INFO_HEIGHT = 15

    def __init__(self, e):
        super(VideoEntry, self).__init__()

        self.get_style_context().add_class('video_entry')

        self._grid.set_size_request(-1, self._ENTRY_HEIGHT)

        x_pos = 0

        img = Gtk.Image()
        img.set_from_file('media/images/test.svg')
        img.set_size_request(self._ENTRY_HEIGHT, self._ENTRY_HEIGHT)
        img.get_style_context().add_class('thumb')
        self._grid.attach(img, x_pos, 0, 1, 4)
        x_pos += 1

        """
        button = Gtk.Button('FS')
        button.set_size_request(20, self._ENTRY_HEIGHT)
        button.connect('clicked', play_video, e['video_url'], e['local_path'], True)
        self.attach(button, x_pos, 0, 1, 3)
        x_pos += 1
        """

        title_str = e['title'] if len(e['title']) <= 70 else e['title'][:67] + '...'
        label = Gtk.Label(title_str)
        label.set_size_request(-1, self._TITLE_HEIGHT)
        label.get_style_context().add_class('title')
        self._grid.attach(label, x_pos, 0, 1, 1)

        info_grid = Gtk.Grid()
        info_grid.set_size_request(-1, self._INFO_HEIGHT)
        info_grid.get_style_context().add_class('info')
        self._grid.attach(info_grid, x_pos, 2, 1, 1)

        if e['local_path'] is None:
            desc_str = e['description'] if len(e['description']) <= 70 else e['description'][:67] + '...'
            label = Gtk.Label(desc_str)
            label.set_size_request(-1, self._DESC_HEIGHT)
            self._grid.attach(label, x_pos, 1, 1, 1)

            duration_str = 'DURATION: {}:{}'.format(e['duration_min'], e['duration_sec'])
            label = Gtk.Label(duration_str)
            label.set_size_request(50, self._INFO_HEIGHT)
            info_grid.attach(label, 0, 0, 1, 1)

            info_grid.attach(Spacer(), 1, 0, 1, 1)

            viewcount_str = 'VIEWS: {}K'.format(int(e['viewcount'] / 1000.0))
            label = Gtk.Label(viewcount_str)
            label.set_size_request(50, self._INFO_HEIGHT)
            info_grid.attach(label, 2, 0, 1, 1)

            info_grid.attach(Spacer(), 3, 0, 1, 1)

            author_str = 'AUTHOR: {}'.format(e['author'])
            label = Gtk.Label(author_str)
            label.set_size_request(100, self._INFO_HEIGHT)
            info_grid.attach(label, 4, 0, 1, 1)

        button = Gtk.Button('Watch video')
        button.set_size_request(self._ENTRY_HEIGHT, self._INFO_HEIGHT)
        button.get_style_context().add_class('play')
        self._button_handler_id = button.connect('clicked', self._play_handler, e['video_url'], e['local_path'], False)
        info_grid.attach(button, 0, 1, 1, 1)

        info_grid.attach(Spacer(), 1, 1, 1, 1)

        button = Gtk.Button('Add to playlist')
        button.set_size_request(self._ENTRY_HEIGHT, self._INFO_HEIGHT)
        button.get_style_context().add_class('play')
        self._button_handler_id = button.connect('clicked', add_to_playlist_handler, 'test.json', e)
        info_grid.attach(button, 2, 1, 1, 1)

    def _play_handler(self, _button, _url, _localfile, _fullscreen):
        _button.set_label('Stop video')
        _button.get_style_context().add_class('playing')
        _button.disconnect(self._button_handler_id)
        self._button_handler_id = _button.connect('clicked', self._stop_handler, _url, _localfile, _fullscreen)
        Gtk.main_iteration()
        play_video(_button, _url, _localfile, _fullscreen)

    def _stop_handler(self, _button, _url, _localfile, _fullscreen):
        _button.set_label('Watch video')
        _button.get_style_context().remove_class('playing')
        _button.disconnect(self._button_handler_id)
        self._button_handler_id = _button.connect('clicked', self._play_handler, _url, _localfile, _fullscreen)
        Gtk.main_iteration()
        stop_videos(_button)


class VideoList(Gtk.EventBox):
    _LIST_HEIGHT = 400

    def __init__(self, videos=None):
        super(VideoList, self).__init__()

        self.get_style_context().add_class('video_list')

        self._grid = Gtk.Grid()
        self._grid.set_row_spacing(10)
        self._grid.set_size_request(-1, self._LIST_HEIGHT)

        align = Gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        padding = 20
        align.set_padding(padding, padding, padding, padding)
        align.add(self._grid)

        self.add(align)

        if videos is not None:
            i = 0
            for v in videos:
                entry = VideoEntry(v)
                self._grid.attach(entry, 0, i, 1, 1)
                i += 1


class VideoListLocal(VideoList):

    def __init__(self, open_folder_dialog=False):
        super(VideoListLocal, self).__init__()

        self.get_style_context().add_class('video_list_local')

        if open_folder_dialog:
            local_dir = self.dir_dialog()
        else:
            local_dir = '/usr/share/kano-video/media/videos'

        files = list_dir(local_dir)
        files = [f for f in files if f[-3:] == 'mkv']
        print files

        if files:
            for i, f in enumerate(files):
                fullpath = os.path.join(local_dir, f)
                filename = os.path.splitext(f)[0]

                title_str = filename if len(filename) <= 40 else filename[:37] + '...'
                e = {'title': title_str,
                     'video_url': None,
                     'local_path': fullpath}

                entry = VideoEntry(e)
                self._grid.attach(entry, 0, i + 1, 1, 1)


class VideoListYoutube(VideoList):

    def __init__(self, keyword=None, username=None, playlist=None):
        super(VideoListYoutube, self).__init__()

        self.get_style_context().add_class('video_list_youtube')

        entries = None

        if keyword:
            entries = search_youtube_by_keyword(keyword)
            print 'searching by keyword: ' + keyword
        elif username:
            entries = search_youtube_by_user(username)
            print 'listing by username: ' + username
        elif playlist:
            entries = playlist
            print 'listing playlist: ' + playlist
        else:
            entries = search_youtube_by_user('KanoComputing')
            print 'listing default videos by KanoComputing'

        if entries:
            parsed_entries = parse_youtube_entries(entries)
            for i, e in enumerate(parsed_entries):
                e['local_path'] = None

                x = Playlist('test')
                x.add(e)
                x.save_to_file('playlists/vid.json')

                entry = VideoEntry(e)
                self._grid.attach(entry, 0, i, 1, 1)
