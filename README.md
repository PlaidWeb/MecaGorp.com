# MecaGorp.com
The record label that is bigger than you

## Editing the site

This site is currently built using [Publ](https://publ.beesbuzz.biz/) with the main repository [on GitHub](https://github.com/PlaidWeb/MecaGorp.com). In order to edit content, you'll need to install [Python](https://python.org/) and [poetry](https://python-poetry.org/).

It is highly recommended that you use macOS, Linux, or WSL, although it *should* work from Windows as well.

The `./run.sh` script will launch the website locally at `http://localhost:5000`. If that port is unavailable, you can use the `-p` commandline argument to specify an alternate port (i.e. `-p 8888` will put the site at `http://localhost:8888`).

When writing a blog post, please start the filename with the publication date, and run the `./fixnames.sh` script to automatically update all entry filenames before checking in.

## Entry metadata

The following entry types are defined:

* `spec`: A format specification
* `sidebar`: An article that appears in the sidebar
* `link`: An external link to be displayed in the sidebar

Currently the following custom metadata fields are supported:

* `Author`: The name of the author of a post
* `Author-URL`: The author's website
* `Version`: The short name of a specification version
* `Group`: The nesting group for a specification in the sidebar

