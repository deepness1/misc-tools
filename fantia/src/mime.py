import mimetypes


def guess_extension(mimetype, url):
    known = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
    }
    ext = known.get(mimetypes) or mimetypes.guess_extension(mimetype, strict=True)
    if ext:
        return ext

    try:
        path = urlparse(download_url).path
        return os.path.splitext(path)[1]
    except IndexError:
        return ".unknown"
    return extension
