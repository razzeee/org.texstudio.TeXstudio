import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class LauncherTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.models = self.directory / "ngrams"

    def launch(self, source=None):
        binary_directory = self.directory / "bin"
        binary_directory.mkdir()
        for name, body in {
            "java": "Path(os.environ['JAVA_ARGS']).write_text(json.dumps(sys.argv[1:]))",
            "texstudio": """
for attempt in range(100):
    if Path(os.environ['JAVA_ARGS']).exists():
        break
    time.sleep(0.01)
Path(os.environ['TEXSTUDIO_ARGS']).write_text(json.dumps(sys.argv[1:]))
""",
            "pkill": "Path(os.environ['PKILL_ARGS']).write_text(json.dumps(sys.argv[1:]))",
        }.items():
            executable = binary_directory / name
            executable.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys, time\nfrom pathlib import Path\n" + body + "\n"
            )
            executable.chmod(0o755)

        if source is None:
            source = (Path(__file__).resolve().parents[1] / "texstudio.sh").read_text()
        source = source.replace("/app/jre/bin/java", str(binary_directory / "java"))
        source = source.replace("/app/ngrams", str(self.models))
        source = source.replace("/app/texlive", str(self.directory / "texlive"))
        launcher = self.directory / "launcher.sh"
        launcher.write_text(source)
        environment = os.environ | {
            "PATH": f"{binary_directory}:{os.environ['PATH']}",
            "JAVA_ARGS": str(self.directory / "java.json"),
            "TEXSTUDIO_ARGS": str(self.directory / "texstudio.json"),
            "PKILL_ARGS": str(self.directory / "pkill.json"),
        }
        subprocess.run(
            ["bash", str(launcher), "file with spaces.tex", "--line", "23"],
            env=environment, check=True, timeout=10, capture_output=True,
        )
        self.assertEqual(
            json.loads((self.directory / "texstudio.json").read_text()),
            ["file with spaces.tex", "--line", "23"],
        )
        self.assertEqual(
            json.loads((self.directory / "pkill.json").read_text()),
            ["-SIGKILL", "java"],
        )
        return json.loads((self.directory / "java.json").read_text())

    def test_missing_language_model_directory(self):
        arguments = self.launch()
        self.assertNotIn("--languageModel", arguments)
        self.assertEqual(arguments[-3:], ["--port", "8081", "--allow-origin"])

    def test_existing_language_model_directory(self):
        self.models.mkdir()
        arguments = self.launch()
        self.assertEqual(arguments[-2:], ["--languageModel", str(self.models)])


if __name__ == "__main__":
    unittest.main()
