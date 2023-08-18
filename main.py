from downloader import RaveDJ_Downloader

# Create an instance
downloader = RaveDJ_Downloader()

prompt1 = input('Single or Batch Mash-Up? Use characters S/B. \n')

if prompt1 == 'S':
    downloader.process_mashup()

elif prompt1 == 'B':
    downloader.process_bulk_mashups()

else:
    print("Please enter a valid response. Program will terminate")
    downloader.close()
