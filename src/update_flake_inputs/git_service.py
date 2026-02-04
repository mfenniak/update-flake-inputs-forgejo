"""Service for interacting with Git."""

import os
import subprocess
import sys
import time
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitService:
    """Service for interacting with Git."""

    private_key: str
    public_key: str
    path: Path

    __key_directory: tempfile.TemporaryDirectory = None
    __scope: str = "--local"

    def __post_init__(self) -> None:
        self.__configure_commit_signing()

    def __configure_commit_signing(self) -> None:
        if self.private_key != None and self.public_key != None:
            self.__key_directory = tempfile.TemporaryDirectory(prefix="git-ssh-")

            keyFile = Path(self.__key_directory.name) / "signing_key"
            pubkeyFile = Path(self.__key_directory.name) / "signing_key.pub"

            with open(keyFile, "w") as f:
                f.write(self.private_key)
                f.write('\n')
            with open(pubkeyFile, "w") as f:
                f.write(self.public_key)
                f.write('\n')

            os.chmod(keyFile, 0o600)
            os.chmod(pubkeyFile, 0o644)

            subprocess.run(
                ["git", "config", "set", self.__scope, "user.signingkey", pubkeyFile],
                cwd=self.path,
                check=True,
            )

            subprocess.run(
                ["git", "config", "set", self.__scope, "gpg.format", "ssh"],
                cwd=self.path,
                check=True,
            )

            subprocess.run(
                ["git", "config", "set", self.__scope, "commit.gpgsign", "true"],
                cwd=self.path,
                check=True,
            )
