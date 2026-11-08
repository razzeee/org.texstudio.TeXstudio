import hashlib
from pathlib import Path
import runpy
import tempfile
import unittest


generate_sources = runpy.run_path(
    Path(__file__).resolve().parents[1] / "generate-maven-sources.py"
)["generate_sources"]


class MavenSourcesTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repository = Path(temporary.name)

    def add_artifact(self, name, remote="central"):
        directory = self.repository / "org/example/example/1.0"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / name).write_bytes(b"artifact")
        with (directory / "_remote.repositories").open("a") as marker:
            marker.write(f"{name}>{remote}=\n")

    def test_generates_sorted_checksummed_sources(self):
        self.add_artifact("example-1.0.pom")
        self.add_artifact("example-1.0.jar")
        self.add_artifact("example-1.0.jar")
        (self.repository / "untracked.jar").write_bytes(b"not downloaded")
        sources = generate_sources(self.repository)
        self.assertEqual(len(sources), 2)
        self.assertEqual(
            [source["dest-filename"] for source in sources],
            ["example-1.0.jar", "example-1.0.pom"],
        )
        self.assertEqual(
            sources[0],
            {
                "type": "file",
                "url": "https://repo.maven.apache.org/maven2/org/example/example/1.0/example-1.0.jar",
                "sha256": hashlib.sha256(b"artifact").hexdigest(),
                "dest": "m2/repository/org/example/example/1.0",
                "dest-filename": "example-1.0.jar",
            },
        )

    def test_rejects_other_repositories(self):
        self.add_artifact("example-1.0.jar", remote="another-repository")
        with self.assertRaisesRegex(ValueError, "Unexpected repository"):
            generate_sources(self.repository)

    def test_accepts_maven_repository_context_suffix(self):
        self.add_artifact("example-1.0.jar", remote="central-" + "a" * 40)
        self.assertEqual(len(generate_sources(self.repository)), 1)

    def test_rejects_unhandled_artifact_types(self):
        self.add_artifact("example-1.0.exe")
        with self.assertRaisesRegex(ValueError, "Unexpected artifact type"):
            generate_sources(self.repository)

    def test_rejects_empty_repository(self):
        with self.assertRaisesRegex(ValueError, "No downloaded Maven artifacts"):
            generate_sources(self.repository)


if __name__ == "__main__":
    unittest.main()
