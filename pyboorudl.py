from pyboorudl import pyboorudl as pyb
import requests
import json
import datetime
import os
import traceback
import hashlib
import time
import micromath
from sys import argv as args


def log(message: str, severity: int):
    """
    Logs a message to a file named "log.txt" and prints it to the console.

    The message will be prefixed with the current date and time, and a label
    indicating the severity of the message.

    Codes:
    
    - 0: INFO
    - 1: WARNING
    - 2: ERROR
    - 3: CRITICAL

    If the file "log.txt" does not exist, it will be created.

    Args:
        message (str): The message to log.
        severity (int): The severity of the message, with 0 being "INFO", 1 being
            "WARNING", and 2 being "ERROR".
    """
    types = ["INFO", "WARNING", "ERROR", "CRITICAL"]

    msg = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{types[severity]}] {message}"

    if not os.path.exists("log.txt"):
        open("log.txt", "w+").close()

    
    with open("log.txt", "a") as f:
        f.write(msg + "\n")

    
    print(msg)


def check_duplicates(hashes):
    # Check for duplicates and return if there are any
    seen_md5s = set()
    unique_hashes = []
    duplicates_removed = 0

    for h in hashes:
        md5 = h["md5"]
        if md5 not in seen_md5s:
            unique_hashes.append(h)
            seen_md5s.add(md5)
        else:
            hash_path = h["path"]
            log(f"Duplicate file found (keeping first): {hash_path}", 1)
            try:
                os.remove(hash_path)
                duplicates_removed += 1
            except FileNotFoundError:
                log(f"Marked as duplicated but file is not on filesystem!", 1)
                continue

    log(f"Removed {duplicates_removed} duplicates (keeping the first occurrence).", 0)
    json.dump(unique_hashes, open("hashes.json", "w"), indent=4)

    return True if duplicates_removed > 0 else False


def get_group(path, files_per_group):
    current_group = 0

    try:
        files = os.listdir(path)
        for f in files:
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path) and micromath.is_integer(f):
                num_files = len(os.listdir(full_path))

                if num_files > files_per_group:
                    current_group += 1
    except FileNotFoundError:
        pass

    return str(current_group).zfill(4)


def main():
    log("Started.", 0)

    config = json.load(open("config.json"))

    if not os.path.exists("hashes.json"):
        open("hashes.json", "w+").write(json.dumps([]))

    path = config["path"]
    dirs = config["dirs"]
    threads = config["threads"]
    sleep_time = config["sleep_time"]

    boorus = [pyb.GELBOORU, pyb.RULE34]

    pybl = pyb.Downloader(path)

    pybl.set_threads(threads)

    pybl.enable_verbose(config["enable_verbose"])

    # Start downloading
    for booru in boorus:
        pybl.set_booru(booru)
        for d in dirs:
            has_duplicates = False
            if booru not in d["boorus"]:
                continue

            pages = d["pages"]
            limit = d["limit"]

            pybl.set_limit(limit)

            d_name = d['name']
            base_dl_path = os.path.join(path, d_name)
            dl_path = ""
            old_path = ""
            pybl.set_tags(d["include_tags"], d["exclude_tags"])

            page = pages+1
            while page >= 0:
                page -= 1
                log(f"Downloading page {page+1}. (Tags: {pybl.tag_str}, Booru: {booru}, Dir: {d_name})", 0)
                hashes = json.load(open("hashes.json"))

                old_path = dl_path
                dl_path = os.path.join(base_dl_path, get_group(base_dl_path, config["files_per_group"]))

                if old_path != dl_path:
                    pybl.reset_counter()

                pybl.change_download_path(dl_path)
                try:
                    pybl.set_page(page)
                    files_downloaded = pybl.threaded_download(oldest_first=True)

                    if not files_downloaded:
                        log(f"No files found on page {page+1}. (Tags: {pybl.tag_str}, Booru: {booru}, Dir: {d_name})", 1)
                        continue

                    files = files_downloaded[0]

                    num_files = len(files)

                    # Add md5 sum for duplicate checking later.
                    for file in files:
                        log(f"Getting hash for {file['path']}...", 0)
                        with open(file["path"], "rb") as f:
                            #md5 = hashlib.md5(f.read()).hexdigest()
                            hashes.append({
                                "path": file["path"],
                                "md5": file["md5"]
                            })

                    json.dump(hashes, open("hashes.json", "w"), indent=4)

                    has_duplicates = check_duplicates(hashes)

                    # Break in case of duplicates for optimization
                    if has_duplicates:
                        break

                except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                    log(f"Error downloading page {page + 1}: {traceback.format_exc()}", 2)
                    continue
                except json.decoder.JSONDecodeError as e:
                    log(f"No more pages!", 2)
                    break
                except OSError as e:
                    log(f"Critical error happened while downloading: {traceback.format_exc()}", 3)
                    log(f"Path: {dl_path}\nPage: {page + 1}\nBooru: {booru}\nTags: {d['include_tags']}", 3)
                    exit(1)
                except Exception as e:
                    log(f"Unexpected error downloading page {page + 1}: {traceback.format_exc()}", 2)
                    continue

                log(f"Downloaded {num_files} files.", 0)
                log(f"Taking a break...", 0)
                time.sleep(sleep_time)
                log(f"Ready!", 0)
            pybl.clear_tags()
            pybl.reset_counter()

    
    log("Finished.", 0)

if __name__ == "__main__":
    if "check" in args:
        check_duplicates(json.load(open("hashes.json")))
    main()
