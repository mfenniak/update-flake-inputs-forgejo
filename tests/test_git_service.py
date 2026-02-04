"""Tests for GitService."""

import pytest
import re
import subprocess
import tempfile

from pathlib import Path
from update_flake_inputs.git_service import GitService


class TestGitService:
    @pytest.fixture
    def fixtures_path(self) -> Path:
        """Get path to test fixtures."""
        return Path(__file__).parent / "fixtures"

    def test_no_change_when_signing_key_not_provided(
        self,
    ) -> None:
        """Test that config is not changed when no key is provided"""
        with tempfile.TemporaryDirectory(prefix="test-git-service") as temp_dir:
            subprocess.run(["git", "init", "-b", "main"], cwd=temp_dir, check=True)

            cp = subprocess.run(["git", "config", "get", "--local", "user.signingkey"], cwd=temp_dir, check=False)
            assert cp.returncode == 1

            cp = subprocess.run(["git", "config", "get", "--local", "gpg.format"], cwd=temp_dir, check=False)
            assert cp.returncode == 1

            cp = subprocess.run(["git", "config", "get", "--local", "commit.gpgsign"], cwd=temp_dir, check=False)
            assert cp.returncode == 1

            git_service = GitService(
                private_key=None,
                public_key=None,
                path=temp_dir,
            )

            cp = subprocess.run(["git", "config", "get", "--local", "user.signingkey"], cwd=temp_dir, check=False)
            assert cp.returncode == 1

            cp = subprocess.run(["git", "config", "get", "--local", "gpg.format"], cwd=temp_dir, check=False)
            assert cp.returncode == 1

            cp = subprocess.run(["git", "config", "get", "--local", "commit.gpgsign"], cwd=temp_dir, check=False)
            assert cp.returncode == 1

    def test_git_config_when_signing_key_is_provided(
        self,
        fixtures_path: Path,
    ) -> None:
        """Test that config set correctly when key is provided"""

        key = (fixtures_path / "ssh-key" / "git-signing-key").read_text().strip()
        pubkey = (fixtures_path / "ssh-key" / "git-signing-key.pub").read_text().strip()
        allowed_signers_file = (fixtures_path / "ssh-key" / "allowed_signers")

        with tempfile.TemporaryDirectory(prefix="test-git-service") as temp_dir:
            subprocess.run(["git", "init", "-b", "main"], cwd=temp_dir, check=True)

            cp = subprocess.run(["git", "config", "get", "--local", "user.signingkey"], cwd=temp_dir, check=False)
            assert cp.returncode == 1

            cp = subprocess.run(["git", "config", "get", "--local", "gpg.format"], cwd=temp_dir, check=False)
            assert cp.returncode == 1

            cp = subprocess.run(["git", "config", "get", "--local", "commit.gpgsign"], cwd=temp_dir, check=False)
            assert cp.returncode == 1

            git_service = GitService(
                private_key=key,
                public_key=pubkey,
                path=temp_dir,
            )

            cp = subprocess.run(["git", "config", "get", "--local", "user.signingkey"], cwd=temp_dir, check=False)
            assert cp.returncode == 0

            cp = subprocess.run(["git", "config", "get", "--local", "gpg.format"], cwd=temp_dir, check=False)
            assert cp.returncode == 0

            cp = subprocess.run(["git", "config", "get", "--local", "commit.gpgsign"], cwd=temp_dir, check=False)
            assert cp.returncode == 0

            with open(Path(temp_dir) / "change.txt", 'w') as file:
                file.write("Signed commit\n")

            subprocess.run(["git", "add", "change.txt"], cwd=temp_dir, check=True)
            subprocess.run(["git", "commit", "-m", "Signed commit"], cwd=temp_dir, check=True)


            subprocess.run(
                ["git", "config", "set", "--local", "gpg.ssh.allowedsignersfile", str(allowed_signers_file)],
                cwd=temp_dir,
                check=True
            )
            cp = subprocess.run(
                ["git", "log", "--show-signature", "-n", "1", "--pretty='format:%G?'"],
                cwd=temp_dir,
                check=True,
                capture_output=True,
            )

            signature_status = cp.stdout.decode('UTF-8').strip()
            assert re.search(r"'format:G'", signature_status)
