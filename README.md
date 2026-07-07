# normifiasongably

This tool normalizes music to -14LUFS, with several caveats:
1. Don't use compression. If a song averages below -14LUFS but has a true peak that would clip if the appropriate gain is applied, just get as close to -14LUFS as possible without clipping.
2. Maintain consistent levels throughout an album. An album's LUFS rating is an average of the whole and each song receives the same gain adjustment.
3. Convert all files to VBR 0 MP3's, even if no gain changes are applied.
