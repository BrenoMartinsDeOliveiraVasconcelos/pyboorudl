import pyboorudl
import platform


def generate_user_agent(user: str):
    return f"pyboorudl-client on {platform.system()} (User indentified by {user})"


def main():
    print(generate_user_agent("test"))


if __name__ == "__main__":
    main()
