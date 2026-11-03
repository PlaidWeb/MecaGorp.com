Title: Ecosystem design
Summary: How the various parts might fit together
Path-Canonical: /whitepapers/ecosystem
Date: 2026-11-02 16:23:28-08:00
UUID: a3612689-68d7-4c2e-a85f-4d3072a2f669
Entry-ID: 32

[Chorus](/chorus/) is, by design, just one piece of a larger puzzle of how the world of post-corporate music streaming can work. Here are a few high-level descriptions of how this can all fit together.

.....

### Chorus receiver

The primary use case for Chorus is providing people a means of subscribing directly to artists' output to put it into their music collection, to then be played through their own mobile app. The intention is that the subscribed music would then become a part of their collection that can be played at any time, living alongside their purchases from other platforms.

To this end, a Chorus receiver would be a piece of software that connects to the Internet and subscribes to a number of Chorus feeds. This could be a single-user instance, or it could support multiple users, and provide the ability for the users to select music to put into their collections. The receiver would then track individuals' music play activities for the purposes of discovery and determining [fair payments](19) or making purchase suggestions.

Playback could occur from a browser-based application or, more likely, via connected applications.

The receiver should also handle caching and transcoding of music files, both to support lower-bandwidth connections and also to avoid overwhelming a popular musician's webserver or causing them a large bandwidth bill.

### openSubsonic integration

[openSubsonic](https://opensubsonic.netlify.app) is a client protocol for connecting a player application to a collection. At its core it is basically a means of streaming an iTunes-style collection to a mobile device, and it is supported by a number of existing music collection servers, such as [Subsonic](https://subsonic.org/) and [Navidrome](https://www.navidrome.org/), and some sales channels such as [Bandcamp](https://bandcamp.com/) support the protocol as well.

There are also quite a few player applications that work with openSubsonic, but they tend to either only support a single collection at a time, or at best treat each collection as a separate "silo" without the ability to browse and play music from multiple collections simultaneously.

To that end, an openSubsonic aggregator could connect as a client to multiple openSubsonic accounts, and would send the same query to each account, aggregating the results together into a single view for the player application. It could also allow setting a priority for which sources take precedence when multiple sources have the same items (for example, most listeners would want to use purchased content from Navidrome or Bandcamp before going with the versions that come from a Chorus feed).

Such an aggregator would be easy to self-host or to provide as a community-hosted option.

Ideally, the aggregator would also have a Chorus receiver built-in, to reduce the complexity of an individual user's setup; this would allow users to only have to connect to a single receiver, and configure it with a connection to their private collection infrastructure. For that matter, it could also be where the private collection is hosted.

There is a lot of flexibility in how this may be implemented.

### Internet radio stations

Another potential use case for Chorus is to provide a means for Internet radio stations (i.e. shared livestreams) to get the latest releases from new artists and then add it to various playlists that are on continuous broadcast.

In this setup, Internet radio stations could subscribe to participating musicians' Chorus feeds directly (and download the files and metadata that way), which would be simple to integrate with most existing Internet radio systems (such as [Icecast](https://icecast.org/) or [AzuraCast](https://icecast.org/)).

### Other platform integrations

In theory it should be straightforward to have a Chorus receiver also adapt its discovered content into ActivityPub, such as for [Funkwhale](https://funkwhale.audio), [Bandwagon](https://bandwagon.fm/), or any of the many other efforts to put music on the Fediverse.
