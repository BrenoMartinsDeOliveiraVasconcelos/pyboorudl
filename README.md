# PyBooru Downloader

That's a module made to download stuff from a booru-like website. Currently, these boorus are supported:

| Booru | Needs token? | Type | URL | Constant* 
|---|---|---|---|---
| Rule34 | No | Hentai | rule34.xxx | ```<module>.RULE34```
| Gelbooru | Yes | Hentai | gelbooru.com | ```<module>.GELBOORU```
| e621 | Yes | Furry Hentai | e621.net | ```<module>.E621```
| Safebooru | No | Anime SFW | safebooru.org | ```<module>.SAFEBOORU```

*The constant column indicates the constant used to set the booru where ```Downloader``` class will download stuff.
