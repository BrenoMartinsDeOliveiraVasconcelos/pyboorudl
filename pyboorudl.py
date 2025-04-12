import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor
import time

# CONSTANTS

RULE34 = "rule34"
GELBOORU = "gelbooru"

class UrlBuilder:
    def __init__(self, endpoint: str, tag_str: str, json: str, page: int, limit: int, post_id: int, cid: int, ignore_post_id: bool, ignore_post_cid: bool):
        self.endpoint = endpoint
        self.tag_str = tag_str
        self.json = json
        self.page = page
        self.limit = limit
        self.id = post_id
        self.cid = cid

        self.ignore_post_id = ignore_post_id
        self.ignore_post_cid = ignore_post_cid


    def build_url(self) -> str:
        """
        Builds a URL for the Rule34/Gelbooru API query using the class's properties.

        This method will construct a URL based on the class's properties and return it as a string. The properties used are the endpoint, json, page, limit, tag_str, id, cid, ignore_post_id, and ignore_post_cid.

        Returns:
            str: The constructed URL.
        """
        url = f"{self.endpoint}&json={self.json}&pid={self.page}&limit={self.limit}"

        if self.tag_str != "":
            url += f"&tags={self.tag_str}"

        if not self.ignore_post_id:
            url += f"&id={self.id}"

        if not self.ignore_post_cid:
            url += f"&cid={self.cid}"

        return url
    

class HttpRequest:
    def __init__(self, retry: int = 3, timeout: int = 60):
        self.url = ""
        self.retry = retry
        self.timeout = timeout


    def set_url(self, url: str):
        """
        Sets the URL to perform the GET request on.

        Args:
            url (str): The URL to set.

        Returns:
            None
        """
        self.url = url

    
    def get(self):
        """
        Performs a GET request on the URL set in the HttpRequest object.

        This method will retry the GET request up to the retry limit if a connection error or HTTP error occurs. The retry limit can be set by passing the retry parameter when creating an HttpRequest object. If the retry limit is exceeded, the method will raise the last exception that occurred.

        Args:
            None

        Returns:
            requests.Response: The response object from the GET request.

        Raises:
            requests.exceptions.ConnectionError: A connection error occurred while performing the GET request and the retry limit was exceeded.
            requests.exceptions.HTTPError: An HTTP error occurred while performing the GET request and the retry limit was exceeded.
        """

        if self.url == "":
            raise Exception("No URL set")

        retry = self.retry
        timeout = self.timeout
        sleep_time = 0

        while True:
            try:
                response = requests.get(self.url)
                response.raise_for_status()
                return response
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                sleep_time += retry

                if sleep_time >= timeout:
                    raise e

                time.sleep(sleep_time)
                continue


class Downloader:
    def __init__(self, download_path: str, selection: str = RULE34, retry: int = 3, timeout: int = 60):
        self.supported_endpoints = {
            "rule34": "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index",
            "gelbooru": "https://gelbooru.com//index.php?page=dapi&s=post&q=index"
        }

        self.different_keys = {
            "gelbooru": {
                "hash": "md5"
                },
            "rule34": {
                "hash": "hash"
                }
        }
        
        self.selection = selection
        self.endpoint = self.supported_endpoints[self.selection]
        self.download_path = download_path
        self.tag_str = ""
        self.json = "1"
        self.post_cid = 0
        self.ignore_post_cid = True
        self.page = 1
        self.post_id = 0
        self.ignore_post_id = True
        self.limit = 100
        self.threads = 5

        self.retry = retry
        self.timeout = timeout
        
        self.content = []
        self.relevant_content = []
        self.md5sum_key = self.different_keys[self.selection]["hash"]



    def set_tags(self, included_tags: list, excluded_tags: list = []):
        """
        Sets the tags for the Rule34/Gelbooru API query. Adds to the existing tag string if already set. Use clear_tags() to reset the tag string.

        This method constructs a tag string by adding included and excluded tags.
        Included tags are prefixed with '+' and excluded tags with '-'.
        The resulting tag string is stored in the `self.tag_str` attribute.

        Args:
            included_tags (list): A list of tags to include in the search.
            excluded_tags (list, optional): A list of tags to exclude from the search.
        """

        # Add included tags
        for tag in included_tags:
            self.tag_str += f"+{tag}"

        # Add excluded tags
        for tag in excluded_tags:
            self.tag_str += f"+-{tag}"

        # Remove first + if it exists
        self.tag_str = self.tag_str[1:] if self.tag_str.startswith("+") else self.tag_str

    
    def clear_tags(self):
        """
        Clears the tag string for the Rule34/Gelbooru API query.
        """
        self.tag_str = ""


    def set_cid(self, cid: int):
        """
        Sets the post change ID for the Rule34/Gelbooru API query. Value is Unix time, so it will probably have posts with same ID.

        Args:
            cid (int): The post ID to search for.
        """
        self.post_cid = cid
        self.ignore_post_cid = False

    
    def unset_cid(self):
        """
        Resets the post ID and ignores it in the Rule34/Gelbooru API query.
        """
        self.post_cid = 0
        self.ignore_post_cid = True


    def set_id(self, id: int):
        """
        Sets the post ID for the Rule34/Gelbooru API query.

        Args:
            id (int): The post ID to search for.
        """
        self.post_id = id
        self.ignore_post_id = False

    
    def unset_id(self):
        """
        Resets the post ID and ignores it in the Rule34/Gelbooru API query.
        """
        self.post_id = 0
        self.ignore_post_id = True

    
    def page_next(self):
        """
        Increments the page number for the Rule34/Gelbooru API query.

        This method increments the page number by one and does not accept any arguments.
        """
        self.page += 1

    
    def page_prev(self):
        """
        Decrements the page number for the Rule34/Gelbooru API query.

        This method decrements the page number by one and does not accept any arguments.
        """
        self.page -= 1

        if self.page < 0:
            self.page = 0


    def set_page(self, page: int):
        """
        Sets the page number for the Rule34/Gelbooru API query.

        Args:
            page (int): The page number to set.
        """
        self.page = page


    def set_limit(self, limit: int):
        """
        Sets the limit of posts fetched for the Rule34/Gelbooru API query.

        Args:
            limit (int): The limit to set.
        """
        self.limit = limit


    def change_download_path(self, path: str):
        """
        Changes the download path for the Rule34/Gelbooru API query.

        Args:
            path (str): The new download path.
        """
        self.download_path = path


    def set_booru(self, booru: str):
        """
        Sets the booru for the Rule34/Gelbooru API query.        height (int): The height of the downloaded file.
response
        Args:
            booru (str): The booru to set.
        """
        self.endpoint = self.supported_endpoints[booru]
        self.selection = booru
        self.md5sum_key = self.different_keys[self.selection]["hash"]


    def set_wait_time(self, wait_time: int, timeout: int = 60):
        """
        Sets the wait time for the Rule34/Gelbooru API query.

        Args:
            wait_time (int): The wait time in seconds.
            timeout (int, optional): The timeout for the API request in seconds.
        """
        self.retry = wait_time
        self.timeout = timeout


    def set_threads(self, threads: int):
        """
        Sets the number of threads to be used as default on threaded_download().

        Args:
            threads (int): The number of threads to use.
        """
        self.threads = threads


    def _generate_url(self):
        return UrlBuilder(self.endpoint, self.tag_str, self.json, self.page, self.limit, self.post_id, self.post_cid, self.ignore_post_id, self.ignore_post_cid).build_url()
    

    def _get_file_info(self, post: dict, file_path: str, file_name: str):
        return {
                    "path": file_path,
                    "name": file_name,
                    "owner": post["owner"],
                    "tags": post["tags"].split(" "),
                    "md5sum": post[self.md5sum_key],
                    "width": post["width"],
                    "height": post["height"],
                    "size": os.stat(file_path).st_size
                }
    

    def _download_post(self, post, make_dir: bool = True):
        if "file_url" in post:

            file_url = post["file_url"]
            file_name = post["image"]
        
            connection = HttpRequest(self.retry, self.timeout)
            connection.set_url(file_url)
            response = connection.get()

            file_path = f"{self.download_path}/{file_name}"

            if make_dir:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(response.content)

            return self._get_file_info(post, file_path, file_name)
        else:
            return False

    def fetch(self, threaded: bool = False) -> list:
        """
        Fetches the posts from the Rule34/Gelbooru API and returns a list of dictionaries containing the post data. Do not use if you want to download the posts automatically.

        Returns:
            list: A list with the content fetched and relevant content for downloading.
        """
        url = self._generate_url()

        connection = HttpRequest(self.retry, self.timeout)
        connection.set_url(url)
        response = connection.get()

        content = []
        relevant_content = []

        if response.text.strip() not in ("", "[]", "{}"):
            content = json.loads(response.text)
        else:
            return False

        relevant_content = content

        if self.selection == GELBOORU:
            relevant_content = content["post"]

        if not threaded:
            self.content = content
            self.relevant_content = relevant_content

        return [content, relevant_content]
    

    def download(self, make_dir: bool = True) -> list:
        """
        Downloads the posts fetched from the Rule34/Gelbooru API.

        It will return a list with the following elements:
        - A list with dictionaries about each downloaded file containing:
        
        path (str): The path to the downloaded file.
        
        name (str): The name of the downloaded file.
        
        owner (str): The owner of the downloaded file.
        
        tags (list): A list with the tags of the downloaded file.
        
        md5sum (str): The md5sum of the downloaded file.

        width (int): The width of the downloaded file.

        height (int): The height of the downloaded file.

        size (int): The size of the downloaded file in bytes.

        - A list with the content fetched
        - A list with the relevant content fetched from the api

        Args:
            make_dir (bool, optional): Whether to create the directory if it does not exist. Defaults to True.

        Returns:
            list: A list with the files, content fetched and relevant content for downloading.
        """
        self.fetch()

        if not self.content:
            return False

        downloads = []

        for post in self.relevant_content:
            download = self._download_post(post, make_dir)
            if download:
                downloads.append(download)
            else:
                return False
            
        return [downloads, self.content, self.relevant_content]
    

    def threaded_download(self, make_dir: bool = True, threads: int = 0) -> list:
        """
        Downloads the posts fetched from the Rule34/Gelbooru API using multiple threads.

        Args:
            make_dir (bool, optional): Whether to create the directory if it does not exist. Defaults to True.
            threads (int, optional): The number of threads to use. Defaults to 5.

        Returns:
            list: Same as download()
        """

        if threads == 0:
            threads = self.threads

        response = self.fetch(threaded=True)

        content = response[0]
        relevant_content = response[1]

        if not content:
            return False

        downloads = []

        with ThreadPoolExecutor(max_workers=threads) as executor:
            for post in relevant_content:
                download = executor.submit(self._download_post, post, make_dir)
                downloads.append(download.result())

        return [downloads, content, relevant_content]


if __name__ == "__main__":
    print("This is a module and should not be run directly.")
