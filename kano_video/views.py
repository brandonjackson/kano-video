from gi.repository import Gtk

from .bar_ui import TopBar, SearchBar, SearchResultsBar, \
    AddVideoBar, PlayModeBar
from .video_ui import VideoList, VideoListLocal, VideoListYoutube
from .playlist_ui import PlaylistList
from .playlist import playlistCollection


class View(Gtk.EventBox):
    _VIEW_HEIGHT = 400

    def __init__(self):
        super(View, self).__init__()

        self._grid = Gtk.Grid()
        self._grid.set_row_spacing(10)
        self._grid.set_size_request(-1, self._VIEW_HEIGHT)

        align = Gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0, yscale=0)
        padding = 20
        align.set_padding(padding, padding, padding, padding)
        align.add(self._grid)

        self.add(align)


class LocalView(View):

    def __init__(self):
        super(LocalView, self).__init__()

        self._header = AddVideoBar()
        self._grid.attach(self._header, 0, 0, 1, 1)

        self._play_mode = PlayModeBar()
        self._grid.attach(self._play_mode, 0, 1, 1, 1)

        self._list = VideoListLocal()
        self._grid.attach(self._list, 0, 2, 1, 1)


class YoutubeView(View):

    def __init__(self):
        super(YoutubeView, self).__init__()

        self._header = SearchBar(self._search_handler)
        self._grid.attach(self._header, 0, 0, 1, 1)

        self._play_mode = PlayModeBar()
        self._grid.attach(self._play_mode, 0, 1, 1, 1)

        self._list = VideoListYoutube()
        self._grid.attach(self._list, 0, 2, 1, 1)

    def _search_handler(self, _button, search_keyword=None, users=False):
        if search_keyword and search_keyword.get_text():
            self._grid.remove(self._list)
            if users is False:
                self._list = VideoListYoutube(keyword=search_keyword.get_text())
            else:
                self._list = VideoListYoutube(username=search_keyword.get_text())
            self._results_bar = SearchResultsBar(search_keyword.get_text(), '100,000')
            self._grid.attach(self._results_bar, 0, 2, 1, 1)
            self._grid.attach(self._list, 0, 3, 1, 1)
        else:
            self._grid.remove(self._list)
            self._list = VideoListYoutube()
            self._grid.attach(self._list, 0, 2, 1, 1)

        self._grid.show_all()


class PlaylistCollectionView(View):

    def __init__(self, playlist_cb):
        super(PlaylistCollectionView, self).__init__()

        self._header = TopBar('Playlist')
        self._grid.attach(self._header, 0, 0, 1, 1)

        self._vids = PlaylistList(playlistCollection.collection, playlist_cb)
        self._grid.attach(self._vids, 0, 1, 1, 1)


class PlaylistView(View):

    def __init__(self, playlist_name):
        super(PlaylistView, self).__init__()

        self._header = TopBar('Playlist')
        self._grid.attach(self._header, 0, 0, 1, 1)

        """
        self.playlist = Playlist('My Playlist')
        self.playlist.add({'somevalue': './test.json'})
        print self.playlist.playlist
        self.playlist.save_to_file('playlists/new.json')
        """

        self._vids = VideoList(videos=playlistCollection.collection[playlist_name].playlist)
        self._grid.attach(self._vids, 0, 1, 1, 1)


class HomeView(View):

    def __init__(self):
        super(HomeView, self).__init__()

        self._header = TopBar('Home')
        self._grid.attach(self._header, 0, 0, 1, 1)
