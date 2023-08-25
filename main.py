from downloader import RaveDJ_Downloader

downloader = RaveDJ_Downloader()

print("Welcome to RaveDJ Downloader! \n")
print("Make sure you are login to your Spotify account if you are going to use any links from Spotify.\n")

downloader.get_site()
downloader.spotify_tab()
downloader.check_cookies()
downloader.grab_urls()
