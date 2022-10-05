# Plex Extras Thumbnails
Plex does not provide any way to set the thumbnail of an Extra.
We can get around this by manually replacing the generated thumbnail that Plex uses.
The biggest hurdle is that Plex stores the thumbnail in a directory structure generated from SHA1 hashes.
It's impossible to reverse engineer how exactly the hash is generated.
Some experimentation shows that it is likely some combination of the movie the Extra is associated with and the hash of the Extra file itself.
Instead we can search the Plex metadata directory for files that were updated around the same time as when the Extra was added.
Once we find the directory we can overwrite the thumbnail.