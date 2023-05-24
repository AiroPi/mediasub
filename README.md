# mediasub

Allow you to sub to different media (new books, new anime, etc...) by building a source that implement some methods.

## Temporary doc

To use this module, you need to create a class that represent a "source". A source is a website/api/rss flux... that provide new content.
Content can be anything you want. New episode of your favorite series, an article from your favorite blog...

### Implementing a source

A source needs to inherit from the abstract class `mediasub.models.base.Source`.
A source must then implement the following methods :

| method             | description                          |
| ------------------ | ------------------------------------ |
| async \_get_recent | Return the x last contents           |
| async \_search     | Allow to search between the contents |
| async \_all        | Return all the contents available    |

A source can optionally implement the following method(s) :

| method           | description       |
| ---------------- | ----------------- |
| async \_download | Allow to download |

If one of these methods raise `SourceDown`, `source.status` is then set to `Down`. Otherwise, the status is `Up`.

---

Note that `Source` has 3 generic types.

- `RecentT_co` : correspond to what `_get_recent` return.
- `SearchT_co` : correspond to what `_search` and `_all` return (`Iterable[SearchT_co]`)
- `DLT` : correspond to what `_download` take in argument.

There is 3 types instead and 1, because of some types of source.

For example, for a scan source, new contents (`RecentT_co`) can be the chapters, and the content we search (`SearchT_co`) could be the manga. The content we download (`DLT`) may be a page.

The type used for `SearchT_co` and `RecentT_co` must inherit from `models.base.NormalizedObject`.
They must implement a `normalized_name` property that should return the most generic name of the content. This allow multiple sources to avoid duplicate the same content (in case of new episode, etc...)
They must implement a `display` property that represent the display name (user-friendly name) of the content.

`RecentT_co` must inherit from `HistoryContent`.
It must implement an `id` property that is an unique name for the content. This allow to ignore already processed content when `get_recent` is called.

---

`Source.supports_download` is True if the source implement the `_download` method. Otherwise it is False.

Also the methods you implement are not the same than the methods users will call. Be sure to implement methods prefixed with `_`.

---

Check `/examples/basic.py` to see how to sub to a source.

## Sources implementations examples

Some implementations examples are available here :

- https://github.com/Deril-fr/mangabot/tree/main/src/sources
