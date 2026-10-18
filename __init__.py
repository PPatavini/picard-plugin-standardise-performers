"""Standardise Performers (legacy) - Picard 3 port of the Picard 2
"Standardise Performers" plugin (v1.0, Sophist).

Splits multi-instrument performer tags into single instruments and combines
names so e.g. (from 10cc by 10cc track 1):

    Performer [acoustic guitar, bass, dobro, electric guitar and tambourine]: Graham Gouldman
    Performer [acoustic guitar, electric guitar, grand piano and synthesizer]: Lol Creme
    Performer [electric guitar, moog and slide guitar]: Eric Stewart

becomes:

    Performer [acoustic guitar]: Graham Gouldman; Lol Creme
    Performer [bass]: Graham Gouldman
    Performer [dobro]: Graham Gouldman
    Performer [electric guitar]: Eric Stewart; Graham Gouldman; Lol Creme
    Performer [grand piano]: Lol Creme
    Performer [moog]: Eric Stewart
    Performer [slide guitar]: Eric Stewart
    Performer [synthesizer]: Lol Creme
    Performer [tambourine]: Graham Gouldman

The performer tags are also sorted in order to maintain a consistent value
and avoid tags appearing to change even though the base data is equivalent.
"""

import re

PLUGIN_NAME = "Standardise Performers"

standardise_performers_split = re.compile(r", | and ").split

# Value of PluginPriority.HIGH in Picard, used by the original plugin
PRIORITY_HIGH = 100


def standardise_performers(api, track, metadata, track_node, release_node=None):
    for key, values in list(metadata.rawitems()):
        if not key.startswith('performer:') \
                and not key.startswith('~performersort:'):
            continue

        mainkey, subkey = key.split(':', 1)
        if not subkey:
            continue

        instruments = standardise_performers_split(subkey)
        if len(instruments) == 1:
            continue

        api.logger.debug("%s: Splitting Performer [%s] into separate performers",
                         PLUGIN_NAME,
                         subkey,
                         )

        prefixes = []
        words = instruments[0].split()
        for word in words[:]:
            # Only deviation from the original: never consume the last word,
            # so an instrument literally named e.g. "solo" is not turned into
            # an empty key.
            if word not in ['guest', 'solo', 'additional', 'minor'] or len(words) == 1:
                break
            prefixes.append(word)
            words.remove(word)
        instruments[0] = " ".join(words)
        prefix = " ".join(prefixes) + " " if prefixes else ""

        for instrument in instruments:
            newkey = '%s:%s%s' % (mainkey, prefix, instrument)
            for value in values:
                metadata.add_unique(newkey, value)

        del metadata[key]

    # Sort performer metadata to avoid changes in processing sequence
    # creating false changes in metadata
    for key, values in list(metadata.rawitems()):
        if key.startswith('performer:') or key.startswith('~performersort:'):
            metadata[key] = sorted(values)


def enable(api):
    api.register_track_metadata_processor(standardise_performers,
                                          priority=PRIORITY_HIGH)
