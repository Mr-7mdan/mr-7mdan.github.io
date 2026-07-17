import routing
import xbmcgui
import xbmcplugin
from resources.lib.cache import get_cached_or_fetch

plugin = routing.Plugin()

@plugin.route('/')
def index():
    xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(show_parental_guide, 'tt0111161'), xbmcgui.ListItem("The Shawshank Redemption"), True)
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/parental_guide/<imdb_id>')
def show_parental_guide(imdb_id):
    data = get_cached_or_fetch(imdb_id)
    # Process and display the data
    # You'll need to create a custom window or use Kodi's built-in dialogs to show the information

if __name__ == '__main__':
    plugin.run()