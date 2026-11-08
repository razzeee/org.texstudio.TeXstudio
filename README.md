# TeXstudio

[TeXstudio](https://texstudio.org/) is an integrated writing environment for creating LaTeX documents. This is the repository for the TeXstudio Flathub build. Contributions are welcome!

## TeX Live

Requires either TeX Live being installed on the system from your distribution's repositories or the TeX Live Flatpak which you can install by running

`flatpak install flathub org.freedesktop.Sdk.Extension.texlive//25.08`

## LanguageTool dependencies

LanguageTool is built from its GitHub source tag. Anitya continues to track
LanguageTool releases. Updating the source version also requires regenerating
`maven-dependencies.json` so the Flatpak build can run Maven offline.

Extract the new source archive into a clean directory. In an SDK shell with
the OpenJDK 21 extension available, set `packaging_dir` to this repository and
`cache_dir` to a new, empty Maven repository, then run from the source directory:

```sh
patch -p1 < "$packaging_dir/languagetool-os-maven-plugin.patch"
. /usr/lib/sdk/openjdk21/enable.sh
mvn --batch-mode --settings "$packaging_dir/maven-settings.xml" \
  -Dmaven.repo.local="$cache_dir" -DskipTests -Dmaven.gitcommitid.skip=true \
  -pl languagetool-standalone -am package
python3 "$packaging_dir/generate-maven-sources.py" "$cache_dir" \
  > "$packaging_dir/maven-dependencies.json"
```

Update the source URL and checksum in the manifest, then rebuild with Flatpak
Builder to verify the generated dependencies work without network access.
The dependency generator can be tested with `python3 -m unittest discover -s tests`.
OpenJDK 21 is used only to build LanguageTool; the bundled Java runtime is unchanged.

## Reporting bugs

Please report any Flatpak-related issues here. If you are unsure whether the problem is Flatpak-related, feel free to open an issue here.
