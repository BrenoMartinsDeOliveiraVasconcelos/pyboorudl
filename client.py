import pyboorudl
import platform
import re

INTEGER_REGEX = "^[0-9]{1,}$"

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


def ask_something(regex: str, question: str) -> str:
    while True:
        response = input(question)

        if re.match(regex, response):
            return response
        else:
            print("Invalid input")


def introduce():
    boorus = [pyboorudl.RULE34, pyboorudl.GELBOORU, pyboorudl.E621, pyboorudl.SAFEBOORU]

    print("Hello! Welcome to PyBooru Downloader! Let's get started.")
    booru = select_option(boorus, "Select a booru to dowbnload from.")
    
    username = ask_something(, "Insert your username: ")


def generate_user_agent(user: str):
    return f"pyboorudl-client on {platform.system()} (User indentified by {user})"


def main():
    introduce()



if __name__ == "__main__":
    main()
