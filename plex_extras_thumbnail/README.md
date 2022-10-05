# Plex Extras Thumbnails
Plex does not provide any way to set the thumbnail of an Extra.
We can get around this by manually replacing the generated thumbnail that Plex uses.
The biggest hurdle is that Plex stores the thumbnail in a directory structure generated from SHA1 hashes.
It's impossible to reverse engineer how exactly the hash is generated.
Some experimentation shows that it is likely some combination of the movie the Extra is associated with and the hash of the Extra file itself.
Instead we can search the Plex metadata directory for files that were updated around the same time as when the Extra was added.
Once we find the directory we can overwrite the thumbnail.

## Configuration
This tool requires the following config values to be set in `config.json`.

- `PLEX_HOME` - path to the home directory of your Plex install
- `PLEX_SERVER_URL` - URL to your Plex server
- `PLEX_TOKEN` - account authentication token, see [this Plex support page](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) for instructions on how to get your auth token

## Usage
```
usage: set_extra_thumbnail [-h] library title extra_name thumbnail

Replace the thumbnail of an Extra in a Plex library.

positional arguments:
  library     Name of the Plex library which the Extra is in
  title       Title of the movie/show of the Extra
  extra_name  Name of the Extra
  thumbnail   Path to the new thumbnail image or a YouTube link

options:
  -h, --help  show this help message and exit

```