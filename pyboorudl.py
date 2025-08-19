import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor
import time
import random
import hashlib

# CONSTANTS

RULE34 = "rule34"
GELBOORU = "gelbooru"
SAFEBOORU = "safebooru"
E621 = "e621"


def network_verbose(text: str, output: bool=False):
    if output:
        print(text)


def get_hash(path) -> str:
    return hashlib.md5(open(path, "rb").read()).hexdigest()


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

    def build_url(self, page_str: str, needs_json: bool) -> str:
        """
        Builds a URL for the Rule34/Gelbooru/e621 API query using the class's properties.

        This method will construct a URL based on the class's properties and return it as a string. The properties used are the endpoint, json, page, limit, tag_str, id, cid, ignore_post_id, and ignore_post_cid.

        Returns:
            str: The constructed URL.
        """
        json_str = f"&json={self.json}" if needs_json else ""
        url = f"{self.endpoint}{json_str}&{page_str}={self.page}&limit={self.limit}"

        if self.tag_str != "":
            url += f"&tags={self.tag_str}"

        if not self.ignore_post_id:
            url += f"&id={self.id}"

        if not self.ignore_post_cid:
            url += f"&cid={self.cid}"

        return url
    

class HttpRequest:
    def __init__(self, headers: dict, retry: int = 3, timeout: int = 5, verbose: bool = False):
        self.url = ""
        self.retry = retry
        self.timeout = timeout
        self.verbose = verbose
        self.headers = headers


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
        timeout_count = timeout
        sleep_time = 0

        while True:
            network_verbose(f"GET {self.url}", self.verbose)
            try:
                network_verbose(f"GET {self.url} -> FECTHNG", self.verbose)
                response = requests.get(self.url, timeout=timeout, headers=self.headers)
                network_verbose(f"GET {self.url} -> CONTENT FETCHED", self.verbose)
                response.raise_for_status()

                network_verbose(f"GET {self.url} -> SUCCESS", self.verbose)

                return response
            except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                timeout_count -= retry

                network_verbose(f"GET {self.url} -> FAILED! TRYING UNTILL TIMEOUT ({sleep_time}s/{self.timeout}s)", self.verbose)

                if timeout_count <= 0:
                    network_verbose(f"GET {self.url} -> TIMEOUT REACHED", self.verbose)
                    raise e

                network_verbose(f"GET {self.url} -> RETRYING IN {retry}s", self.verbose)
                time.sleep(retry)


class Downloader:
    def __init__(self, download_path: str, user_agent: str, selection: str = RULE34, retry: int = 3, timeout: int = 5):
        self.supported_endpoints = {
            "rule34": "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index",
            "gelbooru": "https://gelbooru.com/index.php?page=dapi&s=post&q=index",
            "safebooru": "https://safebooru.org/index.php?page=dapi&s=post&q=index",
            "e621": "https://e621.net/posts.json?"
        }

        self.username_string = {
            "gelbooru": "user_id",
            "e621": "login"
        }
        
        self.headers = {
            "User-Agent": user_agent
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
        self.download_num = 0
        self.page_str = "pid"

        if self.selection == E621:
            self.page_str = "page"


        self.verbose = False
        self.network_verbose = False

        self.retry = retry
        self.timeout = timeout
        
        self.content = []
        self.relevant_content = []



    def set_tags(self, included_tags: list, excluded_tags: list = []):
        """
        Sets the tags for the Rule34/Gelbooru/e621 API query. Adds to the existing tag string if already set. Use clear_tags() to reset the tag string.

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
        Clears the tag string for the Rule34/Gelbooru/e621 API query.
        """
        self.tag_str = ""


    def set_cid(self, cid: int):
        """
        Sets the post change ID for the Rule34/Gelbooru/e621 API query. Value is Unix time, so it will probably have posts with same ID.

        Args:
            cid (int): The post ID to search for.
        """

        if self.selection not in (E621):
            self.post_cid = cid
            self.ignore_post_cid = False
        else:
            raise Exception("E621 does not support cid")

    
    def unset_cid(self):
        """
        Resets the post ID and ignores it in the Rule34/Gelbooru/e621 API query.
        """
        self.post_cid = 0
        self.ignore_post_cid = True


    def set_id(self, id: int):
        """
        Sets the post ID for the Rule34/Gelbooru/e621 API query.

        Args:
            id (int): The post ID to search for.
        """
        self.post_id = id
        self.ignore_post_id = False

    
    def unset_id(self):
        """
        Resets the post ID and ignores it in the Rule34/Gelbooru/e621 API query.
        """
        self.post_id = 0
        self.ignore_post_id = True

    
    def page_next(self):
        """
        Increments the page number for the Rule34/Gelbooru/e621 API query.

        This method increments the page number by one and does not accept any arguments.
        """
        self.page += 1

    
    def page_prev(self):
        """
        Decrements the page number for the Rule34/Gelbooru/e621 API query.

        This method decrements the page number by one and does not accept any arguments.
        """
        self.page -= 1

        if self.page < 0:
            self.page = 0


    def set_page(self, page: int):
        """
        Sets the page number for the Rule34/Gelbooru/e621 API query.

        Args:
            page (int): The page number to set.
        """
        self.page = page


    def set_limit(self, limit: int):
        """
        Sets the limit of posts fetched for the Rule34/Gelbooru/e621 API query.

        Args:
            limit (int): The limit to set.
        """
        self.limit = limit


    def change_download_path(self, path: str):
        """
        Changes the download path for the Rule34/Gelbooru/e621 API query.

        Args:
            path (str): The new download path.
        """
        self.download_path = path


    def set_booru(self, booru: str, api_key: str = "", user_id: str = ""):
        """
        Sets the booru for the Rule34/Gelbooru/e621 API query.        height (int): The height of the downloaded file.
response
        Args:
            booru (str): The booru to set.
        """
        self.endpoint = self.supported_endpoints[booru]
        self.selection = booru

        if self.selection == E621:
            self.page_str = "page"

        if self.selection in [GELBOORU, E621]:
            if api_key == "" or user_id == "":
                raise Exception(f"API key and user ID are required for {self.selection}")
            
            user_string = self.username_string[self.selection]
            self.endpoint += f"&api_key={api_key}&{user_string}={user_id}"


    def set_wait_time(self, wait_time: int, timeout: int = 5):
        """
        Sets the wait time for the Rule34/Gelbooru/e621 API query.

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


    def enable_verbose(self, state: bool = True):
        """
        Enables or disables verbose mode for the Rule34/Gelbooru/e621 API query.

        Args:
            state (bool, optional): Whether to enable verbose mode. Defaults to True.
        """
        self.verbose = state
        self.network_verbose = state


    def _generate_url(self):
        return UrlBuilder(self.endpoint, self.tag_str, self.json, self.page, self.limit, self.post_id, self.post_cid, self.ignore_post_id, self.ignore_post_cid).build_url(self.page_str, False if self.selection == E621 else True)
    

    def _get_file_info(self, post: dict, file_path: str, file_name: str):
        return {
                    "path": file_path,
                    "name": file_name,
                    "owner": post["owner"],
                    "tags": post["tags"].split(" "),
                    "width": post["width"],
                    "height": post["height"],
                    "size": os.stat(file_path).st_size,
                    "url": post["file_url"],
                    "md5": get_hash(file_path)
                }
    

    def _download_post(self, post, make_dir: bool = True):
        file_str = "file_url"

        if not "file_url" in post and self.selection == E621:
            file_str = "url"
            full_dict = post

            post = post["file"]
            post["image"] = post["url"].split(os.path.sep)[-1]
            post["owner"] = full_dict["uploader_id"]
            post["tags"] = " ".join(full_dict["tags"]["general"])
            post["file_url"] = post["url"]

        if file_str in post:

            file_url = post[file_str]
        
            connection = HttpRequest(self.headers, self.retry, self.timeout, self.network_verbose)
            connection.set_url(file_url)
            response = connection.get()

            file_path = ""
            while True:
                self.download_num += 1
                file_name = str(self.download_num).zfill(20)
                file_path = os.path.join(self.download_path, f"{file_name}."+post["image"].split(".")[-1]) #f"{self.download_path}/{file_name}"

                if not os.path.exists(file_path):
                    break

            if make_dir:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(response.content)

            return self._get_file_info(post, file_path, file_name)
        else:
            return False


    def fetch(self, threaded: bool = False) -> list | bool:
        """
        Fetches the posts from the Rule34/Gelbooru/e621 API and returns a list of dictionaries containing the post data. Do not use if you want to download the posts automatically.

        Returns:
            list: A list with the content fetched and relevant content for downloading.
        """
        url = self._generate_url()

        connection = HttpRequest(self.headers, self.retry, self.timeout)
        connection.set_url(url)
        response = connection.get()

        content = []
        relevant_content = []

        if response.text.strip() not in ("", "[]", "{}"):
            content = json.loads(response.text)
        else:
            return False

        relevant_content = content

        if self.selection in (GELBOORU):
            try:
                relevant_content = content["post"]
            except KeyError:
                return False
            
        if self.selection in (E621):
            relevant_content = content["posts"]

        if not threaded:
            self.content = content
            self.relevant_content = relevant_content

        return [content, relevant_content]
    

    def threaded_download(self, make_dir: bool = True, threads: int = 0, oldest_first: bool = False) -> list | bool:
        """
        Downloads posts from the Rule34/Gelbooru/e621 API using multiple threads. The page downloaded is set using the set_page() method.

        It will return a list with the following elements:
        - A list with dictionaries about each downloaded file containing:
        
        path (str): The path to the downloaded file.
        
        name (str): The name of the downloaded file.
        
        owner (str): The owner of the downloaded file.
        
        tags (list): A list with the tags of the downloaded file.


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

        if threads == 0:
            threads = self.threads

        response = self.fetch(threaded=True)

        if not response:
            return False

        content = response[0] # type: ignore
        relevant_content = response[1] # type: ignore

        if oldest_first:
            relevant_content.reverse()

        if not content:
            return False

        downloads = []

        total = len(relevant_content) 
        count = 0
        percent = 0

        with ThreadPoolExecutor(max_workers=threads) as executor:
            for post in relevant_content:
                if self.verbose:
                    count += 1
                    percent = (count / total) * 100

                    print(f"Downloading post {count}/{total} on page {self.page} with tags: {self.tag_str} ({percent:.2f}%)")

                try:
                    download = executor.submit(self._download_post, post, make_dir)
                    if download:
                        downloads.append(download.result())
                except Exception as e:
                    continue

        return [downloads, content, relevant_content]
    

    def loop_download(self, start_page: int, end_page: int, make_dir: bool = True, threaded: bool = True, threads: int = 0) -> list:
        """
        Download automatically a range of pages. By default, downloads on thread. Set threaded to false to disable threading.
        
        Note: The self.page attribute will be set to the last page downloaded.

        Args:
            start_page (int): The start page to download. (Paging starts at 0)
            end_page (int): The end page to download. (This will be the last page downloaded)
            make_dir (bool, optional): Whether to create the directory if it does not exist. Defaults to True.
            threaded (bool, optional): Whether to use threading. Defaults to True.
            threads (int, optional): The number of threads to use. Defaults to 5.

        Returns:
            list: List of resulting outputs of threaded_download()
        """

        self.set_page(start_page)
        
        if threads > 0:
            self.set_threads(threads)
        else:
            threads = self.threads

        if not threaded:
            threads = 1

        outputs = []

        for self.page in range(start_page, end_page+1):
            output = self.threaded_download(make_dir, threads)
            if output:
                outputs.append(output)

        return outputs
    

    def reset_counter(self):
        """
        Resets the download counter.
        """
        self.download_num = 0




if __name__ == "__main__":
    pass
    
