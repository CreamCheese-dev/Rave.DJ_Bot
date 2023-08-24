from downloader import RaveDJ_Downloader

# Create an instance
downloader = RaveDJ_Downloader()

print("Welcome to RaveDJ Downloader! \n")

print("Make sure you are login to your spotify account prior to using this script in order to use their associated links! \n")

downloader.get_site()

downloader.check_cookies()

downloader.grab_urls()
