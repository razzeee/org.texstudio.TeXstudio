#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path
import re


def checksum(path):
    with path.open("rb") as artifact:
        return hashlib.file_digest(artifact, "sha256").hexdigest()


def generate_sources(repository):
    artifacts = set()
    for marker in repository.rglob("_remote.repositories"):
        for line in marker.read_text().splitlines():
            if not line or line.startswith("#"):
                continue
            artifact, remote = line.split("=", 1)[0].rsplit(">", 1)
            if not re.fullmatch(r"central(?:-[0-9a-f]{40})?", remote):
                raise ValueError(f"Unexpected repository {remote!r} in {marker}")
            path = marker.parent / artifact
            if path.suffix not in (".jar", ".pom"):
                raise ValueError(f"Unexpected artifact type: {path}")
            artifacts.add(path.relative_to(repository))

    if not artifacts:
        raise ValueError("No downloaded Maven artifacts found")

    return [
        {
            "type": "file",
            "url": f"https://repo.maven.apache.org/maven2/{artifact.as_posix()}",
            "sha256": checksum(repository / artifact),
            "dest": f"m2/repository/{artifact.parent.as_posix()}",
            "dest-filename": artifact.name,
        }
        for artifact in sorted(artifacts)
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    args = parser.parse_args()
    print(json.dumps(generate_sources(args.repository), indent=2))
