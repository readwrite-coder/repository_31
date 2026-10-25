import yt_dlp
from urllib.parse import urlparse


def get_youtube_title(link):
    # Parse and validate the URL
    parsed_url = urlparse(link)
    domain = parsed_url.netloc.lower().split(":")[0]

    valid_domains = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
        "www.youtu.be",
    }

    if parsed_url.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme.")

    if domain not in valid_domains:
        raise ValueError("This is not a YouTube URL.")

    # Extract video information without downloading it
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(link, download=False)

        if not info or not info.get("title"):
            raise ValueError("Could not retrieve the video title.")

        return info["title"]

    except yt_dlp.utils.DownloadError as error:
        raise ValueError(
            "The YouTube video is invalid, unavailable, "
            "or could not be accessed."
        ) from error


if __name__ == "__main__":

    link = input("Enter a YouTube video URL: ")

    try:
        title = get_youtube_title(link)
        print("Video title:", title)
    except ValueError as error:
        print("Error:", error)

