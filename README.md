# PyBooru Downloader Documentation

That's a module made to download stuff from a booru-like website. Currently, these boorus are supported:

| Booru | Needs token? | Type | URL | Constant* 
|---|---|---|---|---
| Rule34 | Yes | Hentai | rule34.xxx | ```<module>.RULE34```
| Gelbooru | Yes | Hentai | gelbooru.com | ```<module>.GELBOORU```
| e621 | Yes | Furry Hentai | e621.net | ```<module>.E621```
| Safebooru | No | Anime SFW | safebooru.org | ```<module>.SAFEBOORU```

*The constant column indicates the constant used to set the booru where ```Downloader``` class will download stuff.

**Note: You can run client.py if you don't know programming or just don't want to make your own client.**

## 1 Setup

If you are whiling to download from a booru that needs a token, you need to get an API token and your user ID to do so. Here's a brief tutorial on how to get it.

Note: You need to be logged in on the desired booru.

#### 1.1 Rule34

- Access [options](https://rule34.xxx/index.php?page=account&s=options)
- On **API Access Credentials**, check that little checkbox under the text input box
- Scroll to the end and click **Save** 
- Refresh the page
- Back to **API Access Credentials**, copy and paste that text on input box and save it on a secure place

How it should look like: 

```&api_key=API&user_id=NUMERIC_ID ```

```API``` and ```NUMERIC_ID``` are placeholders. API is your API token and NUMERIC_ID is your user ID.

#### 1.2 Gelbooru

- Access [options](https://gelbooru.com/index.php?page=account&s=options)
- On **API Access Credentials**, copy and paste that text on input box and save it on a secure place.

How it should look like: 

```&api_key=API&user_id=NUMERIC_ID ```

```API``` and ```NUMERIC_ID``` are placeholders. API is your API token and NUMERIC_ID is your user ID.

#### 1.3 e621

- Access [edit profile](https://e621.net/users/1550978/edit)
- On **API Key**, click **Generate**
- Type your password
- Copy and paste your **API Key** on a secure place.

**Note: Your user ID is your username.**

### 2 Preparation

If you are too lazy to read carefully and/or you are whiling to try to make it work by yourself, here's a working code to you start working with.

```python
import pyboorudl

dl = pyboorudl.Downloader(download_path="download", user_agent="pyboorudl/1.0")

dl.set_booru(pyboorudl.RULE34, api_key="API_KEY", user_id="USER_ID")
dl.set_tags(["yaoi"])
dl.set_page(1)
dl.set_limit(1)

dl.threaded_download()
```

#### 2.1 Declaring the Downloader class

First, you need to declare the Downloader class. You will use it for anything you need. Let's start with this:

```python

dl = pyboorudl.Downloader(download_path="download", user_agent="pyboorudl/1.0")
```

There's two parameters that are mandatory, and the other ones are optional (check docstring for more information). You will need to specify where your files will be downloaded (```download_path```) and your user agent (```user_agent```).

#### 2.2 Specifying booru

Then, you need to specify the booru using ```Downloader().set_booru```. This method receives 3 parameters, but only 1 are needed if you are using a booru that doesn't requires a token.

|Parameter | Description | Expected value 
| --- | --- | ---
|booru | The booru that you want to download from | Booru name (Check constants on the table at begning of README.md)
|api_key | Your API key | String with api key if needed
|user_id | Your used ID | String with your user ID if needed 

#### 2.3 Specifying tags

The tags are not obligatory to download, but maybe you would want to use tags. If so, you need to use the method ```Downloader().set_tags```.

| Paramater | Descripption | Expected value
| --- | --- | ---
| included_tags | The tags you want to download | A list with strings
| excluded_tags | The tags you **DON'T** want to download. Optional | A list with strings

**Note: Don't forget to use _ instead of spaces.**

##### 2.3.1 Clearing the tags

After using it, you may clear your tags if you are whiling to download content with other tags. The method is ```Downloader().clear_tags```. It receives no arguments.

#### 2.4 Specifying the pagge 

It's not mandatory to define a page, but if you don't it will only download the first page. Use the method ```Downloader().set_page```.

| Parameters | Description | Expected value
| --- | --- | ---
| page | Page number | Integer with page number

Note you can also use ```Downnloader().page_next``` and ```Downloader().page_prev``` to navigate between pages.

#### 2.5 Specifying limits

By default, each page has a limit of 100 requests. You can change that with ```Downloader().set_limit```.

| Parameters | Description | Expected value
| --- | --- | ---
| limit | The max content to download per page | Integer with limit

## 3 - Downloading

After configuring it, you can finally download. To do so, there's 2 ways.

### 3.1 Downloading automatically

This is the way you would like to do most of the time. This way, you will need to use ```Downloader().threaded_download``` method to do so. Here's the parameters. Note that none are mandatory.

| Parameters | Description | Expected value
| --- | --- | ---
| threads (*) | The number of threads to use | Integer with the number of threads
| oldest_first | If the page will be downloaded from the oldest item or the newest item | Boolean. Defaults to False
| tags_on_name | If the tags will be included on the filename | Boolean. Defaults to False
| check_duplicates | If duplicates will be checked automatically | Boolean. Defaults to True

*You can also define the thread number with ```Downloader().set_threads```.

**Returns a list with the files, content fetched and relevant content for downloading.**

### 3.2 Download by yourself

If you are not happy with how downloading is implemented, you can call ```Downloader().fetch``` and download content by yourself. It will use all stuff you defined on last steps and fetch content. However, you can always open an issue or a pull request if you want to enhance the code.

| Parameters | Description | Expected value
| --- | --- | ---
| threaded | If it's threaded | Boolean. Defaults to False

**Returns a list with content fetched and relevant content for downloading.**

## 4 Extra stuff that may be useful

This section is not important but contains stuff that may be useful for later.

### 4.1 Reset counter

You can reset the counter for file naming number with the method ```Downloader().reset_counter``` .

### 4.2 Enable/disable verbosity for debugging

If you encounter any issue, you can enable verbosity with ```Downloader().enable_verbose```.

| Parameters | Description | Expected value
| --- | --- | ---
state | Enabled or disabled | Boolean. Defaults to True.


### 4.3 Test connection

You can test the connection with ```Downloader().test_connection```. It returns a boolean.

### 4.4 Set download path

You can set the download path with ```Downloader().set_download_path```

| Parameters | Description | Expected value
| --- | --- | ---
path | The path to the download folder | String
