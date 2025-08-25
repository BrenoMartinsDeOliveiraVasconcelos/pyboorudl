import pyboorudl
import platform
import re
import time


INTEGER_REGEX = "^[0-9]{1,}$"
TAG_REGEX = "^([a-z]|[A-Z]|[_\\/]){1,}$"

def select_option(options: list, menu_desc: str) -> int:
    print(menu_desc)
    
    for i, option in enumerate(options):
        print(f"[{i}] {option}")
    
    selection = -1

    while selection < 0 or selection > len(options):
        selection_input = input("Select an option: ")

        if re.match(INTEGER_REGEX, selection_input):
            selection = int(selection_input)
        else:
            print("Invalid input")

    
    return selection


def ask_something(regex: str | None, question: str, space_split = False, success_if_empty = False, return_when_empty = " ") -> str | list:    
    while True:
        response = input(question)

        if success_if_empty and response == "":
            return return_when_empty

        response_list = response.split(" ") if space_split else [response]
        
        is_input_valid = False

        for item in response_list:
            if regex is None or re.match(regex, item):
                is_input_valid = True
            else:
                print("Invalid input")
                is_input_valid = False
                break

        if is_input_valid:
            return response_list if space_split else response


def introduce():
    boorus = [pyboorudl.RULE34, pyboorudl.GELBOORU, pyboorudl.E621, pyboorudl.SAFEBOORU]

    print("Hello! Welcome to PyBooru Downloader! Let's get started.")
    booru = select_option(boorus, "Select a booru to dowbnload from.")
    
    username = ask_something(None, "Insert your username: ")
    api_key = ""
    user_id = ""

    if boorus[booru] != pyboorudl.SAFEBOORU:
        print("Please follow the instructions on README.md (section 1) and insert API token and User ID.")
        api_key = ask_something(None, "Insert your API token: ")
        user_id = ask_something(None, "Insert your User ID: ")
    
    return [username, api_key, user_id, boorus[booru]]


def generate_user_agent(user: str):
    return f"pyboorudl-client on {platform.system()} (User indentified by {user})"



def initializate_downloader(booru, user_agent, api_key, user_id) -> pyboorudl.Downloader | None:
    downloader = pyboorudl.Downloader(download_path="download", user_agent=user_agent)
    downloader.set_booru(booru, api_key, user_id)

    is_successful = downloader.test_connection()
    downloader.enable_verbose()
    
    return downloader if is_successful else None


def main():
    credentials = introduce()
    user_agent = generate_user_agent(credentials[0])

    dl = initializate_downloader(credentials[3], user_agent, credentials[1], credentials[2])

    if dl is not None:
        included_tags = ask_something(TAG_REGEX, "Insert tags to include (separated by spaces): ", space_split=True, success_if_empty=True, return_when_empty=[])
        excluded_tags = ask_something(TAG_REGEX, "Insert tags to exclude (separated by spaces): ", space_split=True, success_if_empty=True, return_when_empty=[])
        page_range = ask_something(INTEGER_REGEX, "Insert page range separated by spaces (Example 1 10, so it's from page 1 to 10): ", space_split=True)
        limit = ask_something(INTEGER_REGEX, "Insert limit (default is 100): ", success_if_empty=True, return_when_empty="100")
        download_folder = ask_something(None, "Insert download folder (default is download): ", success_if_empty=True, return_when_empty="download")

        dl.set_tags(included_tags, excluded_tags)
        dl.set_download_path(download_folder)
        dl.set_limit(int(limit))

        print("Download is going to start in a few seconds.")
        time.sleep(5)

        for page in range(int(page_range[0])-1, int(page_range[1])):
            dl.set_page(page)
            dl.threaded_download(threads=5, tags_on_name=True, check_duplicates=True)
            time.sleep(1)

    else:
        print("Connection failed. Check your credentials.")



if __name__ == "__main__":
    main()
