from downloader import RaveDJ_Downloader

# Create an instance
downloader = RaveDJ_Downloader()

print("Welcome to RaveDJ Downloader! \n")

downloader.check_cookies()

prompt1 = input('Manual input or text?. Use characters S/B. \n')

if prompt1 == 'S':
    downloader.process_mashup()

elif prompt1 == 'B':
    downloader.process_bulk_mashups()

else:
    print("Please enter a valid response. Program will terminate")
    downloader.close()
