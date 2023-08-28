import re
import os
import sys
import time
import glob
import requests
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import url_changes


# CONSTANTS
SHORT_TIME_OUT = 30
TIME_OUT = 720
POLL_FREQ = 5

class RaveDJ_Downloader:

    def __init__(self):
        self.driver = webdriver.Chrome()

    # --------------------- UTILITY STATIC METHODS ---------------------

    @staticmethod
    def is_valid_youtube_url(url):
        # Matches both individual video links and links with playlist parameters
        video_pattern = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/watch\?v=[\w-]{11}.*')

        # Matches shortened video links
        shortened_video_pattern = re.compile(r'^(https?://)?(www\.)?youtu\.be/[\w-]{11}')

        return bool(video_pattern.match(url)) or bool(shortened_video_pattern.match(url))

    @staticmethod
    def is_valid_spotify_url(url):
        # This regex covers tracks, albums, and playlists only
        pattern = re.compile(r'^https://open\.spotify\.com/(track|album|playlist)/[a-zA-Z0-9]{22}$')

        return bool(pattern.match(url))

    @staticmethod
    def verify_links(url):
        return RaveDJ_Downloader.is_valid_spotify_url(url) or RaveDJ_Downloader.is_valid_youtube_url(url)

    @staticmethod
    def clean_url(url):
        if "youtube" in url:
            match = re.match(r'(https://www\.youtube\.com/watch\?v=[\w-]{11})', url)
            if match:
                return match.group(1)
        return url

    import time

    @staticmethod
    def download_video(url):
        # Split the URL and extract the necessary part
        url_parts = url.split("/")
        # Create the real URL to call the API
        real_url = f"https://api.red.wemesh.ca/mashups/{url_parts[3]}"

        attempts = 0
        max_attempts = 5  # Set a limit to the number of attempts
        video_url = None

        while attempts < max_attempts:
            # Make a GET request to the API
            response = requests.get(real_url)
            response_json = response.json()

            if 'data' in response_json and 'videos' in response_json['data']:
                video_url = response_json['data']['videos'].get('max')
                if video_url:
                    break
            else:
                print("Data not yet available. Waiting...")
                time.sleep(5)  # Wait for 5 seconds before next attempt
                attempts += 1

        if video_url is None:
            print("Failed to retrieve video URL after multiple attempts. Exiting.")

        print(f"MP4 URL: {video_url}")

        # Download the video
        video_response = requests.get(video_url)

        filename_base = "video"
        filename_ext = ".mp4"
        counter = 1
        final_filename = filename_base + filename_ext

        while os.path.exists(final_filename):
            final_filename = f"{filename_base}{counter}{filename_ext}"
            counter += 1

        with open(final_filename, 'wb') as file:
            file.write(video_response.content)

        print("Video downloaded successfully!")

    # --------------------- SITE INTERACTION METHODS ---------------------

    def get_site(self):
        driver = self.driver
        driver.get('https://rave.dj/mix')

    def check_cookies(self):
        driver = self.driver

        try:
            cookies_page = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, 'qc-cmp2-ui'))
            )
            print("Accepting cookies to proceed with page. \n")
            button = cookies_page.find_element(By.CLASS_NAME, 'css-47sehv')
            button.click()
        finally:
            return

    def spotify_tab(self):
        driver = self.driver

        original_tab_handle = driver.current_window_handle

        driver.execute_script("window.open('');")

        driver.switch_to.window(driver.window_handles[-1])

        driver.get("https://accounts.spotify.com/en/login")

        driver.switch_to.window(original_tab_handle)

    def grab_urls(self):

        print("Two song Mash-Up or Playlist? \n")
        type_of_mashup = input("Enter the character 'S' or 'P'. \n")

        # Get a list of all txt files in the current directory
        txt_files = glob.glob("*.txt")

        if not txt_files:  # If there are no txt files in the directory
            print("No .txt files found in the current directory.")
            return

        for filename in txt_files:
            with open(filename, 'r') as f:
                urls = f.readlines()

                index = 0
                successful_url_count = 0  # Counter to keep track of successfully verified and pasted URLs

                while index < len(urls):
                    clean_url = urls[index].strip()  # Remove the newline character

                    if "rave.dj" in clean_url:
                        try:
                            self.download_video(clean_url)
                        except Exception as e:
                            print(
                                f"Error: Could not download the song from the URL {clean_url}. The song might not have been processed. Reason: {e} \n")
                    elif self.verify_links(clean_url):
                        track = self.clean_url(clean_url)
                        self.paste_tracks(track)

                        # If in "S" mode, increment our successful_url_count
                        if type_of_mashup.lower() == 's':
                            successful_url_count += 1

                            # If we've successfully processed 2 URLs, process the mix and reset the counter
                            if successful_url_count == 2:
                                time.sleep(5)  # Wait till track-list is updated
                                self.process_mix()
                                successful_url_count = 0  # Reset the counter

                                self.get_site()  # refresh site
                    else:
                        print('Invalid link. Skipping...')

                    # Always move to next url
                    index += 1

                # If it's "P" mode, process the mashup after all URLs are pasted
                if type_of_mashup.lower() == 'p':
                    time.sleep(5)  # Wait till track-list is updated
                    self.process_mix()

        print("All urls have been reviewed. Program will terminate.")
        self.close()

    def paste_tracks(self, url):

        driver = self.driver

        # Initial count of the songs present in the tracklist
        current_tracks = driver.find_elements(By.XPATH, "//div[contains(@class, 'track-title')]")
        initial_track_count = len(current_tracks)

        # Find search bar
        search = driver.find_element(By.CLASS_NAME, 'search-input')

        # Type in song links
        search.clear()
        search.send_keys(url)
        search.send_keys(Keys.RETURN)

        # Wait for a new track to be added
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//div[contains(@class, 'track-title')]")) > initial_track_count
            )

            # Check the total number of tracks now
            total_tracks = driver.find_elements(By.XPATH, "//div[contains(@class, 'track-title')]")
            new_track_count = len(total_tracks)

            # If the count has increased, it means the new track was added
            if new_track_count > initial_track_count:
                print("New track added:", total_tracks[-1].text)
            else:
                print(f"Failed to add the track from URL: {url}")

        except Exception as e:
            print(f"Track was not detected in the tracklist from URL: {url}. Error message: {str(e)}")

    def process_mix(self):
        driver = self.driver
        initial_url = driver.current_url
        retries = 1  # Number of attempts

        while retries >= 0:
            # Process Mash-Up
            create_btn_css_selector = "button.mix-button.mix-floating-footer.pulsing-glow"
            create_btn = driver.find_element(By.CSS_SELECTOR, create_btn_css_selector)
            create_btn.click()

            try:
                # Wait until URL changes
                wait = WebDriverWait(driver, SHORT_TIME_OUT)
                wait.until(url_changes(initial_url))
                new_url = driver.current_url
                print(f"Mix is in the queue. Assigned URL: {new_url} \n")
                print("Please wait, this could take up to 15 minutes. \n")
                wait = WebDriverWait(driver, TIME_OUT, poll_frequency=POLL_FREQ)
                wait.until(EC.presence_of_element_located((By.ID, 'ForegroundPlayer')))
                print("Mash-up has been successfully processed!, Downloading Now...")
                RaveDJ_Downloader.download_video(new_url)
                break

            except TimeoutException:
                if driver.current_url == initial_url:
                    print("Failed to add tracks to the queue. Retrying...")
                    retries -= 1
                else:
                    print("Mash-up did not load within 15 minutes, saving Rave.DJ URL to text file.")
                    with open('failed_urls.txt', 'a') as file:
                        file.write(driver.current_url + '\n')
                    break

        if retries == 0:
            print(
                "Failed to enter the queue after the retry. Website may be under serious load. Please try again some other time.")

    def close(self):
        self.driver.quit()
        sys.exit()
