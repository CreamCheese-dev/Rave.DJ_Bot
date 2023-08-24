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


class RaveDJ_Downloader:

    def __init__(self):
        self.driver = webdriver.Chrome()

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
    def clean_youtube_url(url):
        match = re.match(r'(https://www\.youtube\.com/watch\?v=[\w-]{11})', url)
        return match.group(1) if match else None

    @staticmethod
    def download_video(url):
        # Split the URL and extract the necessary part
        url_parts = url.split("/")
        # Create the real URL to call the API
        real_url = f"https://api.red.wemesh.ca/mashups/{url_parts[3]}"

        # Make a GET request to the API
        response = requests.get(real_url)
        response_json = response.json()

        # Check if the video URL is present
        video_url = response_json['data']['videos'].get('max')
        if video_url is None:
            print("Wait for the video to finish!")
            return

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

    @staticmethod
    def check_spotify_login(driver):
        if "spotify.com" in driver.current_url:
            return True
        return False

    def get_site(self):
        driver = self.driver
        driver.get('https://rave.dj/mix')

    def check_cookies(self):
        driver = self.driver

        try:
            cookies_page = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, 'qc-cmp2-ui'))
            )
            print("Accepting cookies to proceed with page.")
            button = cookies_page.find_element(By.CLASS_NAME, 'css-47sehv')
            button.click()
        finally:
            return

    def grab_urls(self):
        # Get a list of all txt files in the current directory
        txt_files = glob.glob("*.txt")

        if not txt_files:  # If there are no txt files in the directory
            print("No .txt files found in the current directory.")
            return

        for filename in txt_files:
            with open(filename, 'r') as f:
                urls = f.readlines()

                index = 0
                while index < len(urls):
                    clean_url = urls[index].strip()  # Remove the newline character

                    if "rave.dj" in clean_url:
                        try:
                            self.download_video(clean_url)
                        except Exception:
                            print(
                                f"Error: Could not download the song from the URL {clean_url}. The song might not have been processed.")

                    if self.verify_links(clean_url):
                        track = self.clean_youtube_url(clean_url)

                        self.paste_tracks(track)

                    if not self.verify_links(clean_url):
                        print('Invalid link. Skipping...')

                    # move to next url
                    index += 1  # Move to the next URL

                # Wait till track-list is updated
                time.sleep(5)

                # Proceed to do mash-up
                self.process_mix()

        print("All urls have been reviewed. Program will terminate.")

        self.driver.quit()

    def paste_tracks(self, url):
        driver = self.driver

        # Initial count of the songs present in the tracklist
        current_tracks = driver.find_elements(By.XPATH, "//div[contains(@class, 'track-title')]")
        initial_track_count = len(current_tracks)

        # Find search bar
        search = driver.find_element(By.CLASS_NAME, 'search-input')

        # Type in song links
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

        print("Mix is now being processed. This can take up to 15 minutes. ")

        # Process Mash-Up
        create_btn_css_selector = "button.mix-button.mix-floating-footer.pulsing-glow"
        create_btn = driver.find_element(By.CSS_SELECTOR, create_btn_css_selector)
        create_btn.click()

        # Wait till url updated
        time.sleep(5)
        current_url = driver.current_url

        try:
            # Wait until processed
            wait = WebDriverWait(driver, 750, poll_frequency=5)  # Check every 5 second
            foreground_player_element = wait.until(EC.presence_of_element_located((By.ID, 'ForegroundPlayer')))
            print("Mash-up has been successfully been processed!, Downloading Now...")
            RaveDJ_Downloader.download_video(current_url)

        except TimeoutException:
            print("Mash-up did not load within 15 minutes, saving URL to text file.")
            with open('failed_urls.txt', 'a') as file:
                file.write(current_url + '\n')

    def close(self):
        self.driver.quit()
        sys.exit()
