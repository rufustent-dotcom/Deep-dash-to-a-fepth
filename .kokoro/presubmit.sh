#!/bin/bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Kokoro presubmit script for antigravity-sdk-py.
# Runs unit tests and verifies packaging on every GoB change.

set -euo pipefail

# Resolve SCRIPT_DIR before cd so the relative BASH_SOURCE path is
# resolved against the original working directory (the Kokoro workspace root).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Fallback to local repo root if running outside of Kokoro for local debugging
REPO_ROOT="${KOKORO_ARTIFACTS_DIR:+${KOKORO_ARTIFACTS_DIR}/git/antigravity-sdk-py}"
REPO_ROOT="${REPO_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"

cd "${REPO_ROOT}"

# --- Python 3.10 via pyenv (pre-installed on the Kokoro image) ---
echo "--- Setting up Python 3.10 ---"
eval "$(pyenv init -)"
pyenv install -s 3.10
pyenv global 3.10
python3 --version

echo "--- Installing build tools with hash verification ---"
# Install build/release tools with hash verification.
# See go/pip-install-remediation.
python3 -m pip install \
  --require-hashes \
  --no-deps \
  -r "${SCRIPT_DIR}/requirements-build.txt"

echo "--- Installing runtime and test dependencies with hash verification ---"
# Install all runtime + test dependencies with hash verification.
# The lockfile is generated from pyproject.toml via:
#   pip-compile --allow-unsafe --generate-hashes --extra dev pyproject.toml \
#     -o .kokoro/requirements-test.txt
# See go/pip-install-remediation.
python3 -m pip install \
  --require-hashes \
  --no-deps \
  -r "${SCRIPT_DIR}/requirements-test.txt"

echo "--- Installing package under test ---"
# Install the package itself with --no-deps --no-index since all
# dependencies are already installed above with hash verification.
python3 -m pip install --no-deps --no-index -e .

echo "--- Running tests ---"
PYTEST_ARGS=(-v --tb=short)
if [[ -n "${KOKORO_ARTIFACTS_DIR:-}" ]]; then
  PYTEST_ARGS+=(--junitxml="${KOKORO_ARTIFACTS_DIR}/sponge_log.xml")
fi
python3 -m pytest "${PYTEST_ARGS[@]}"

echo "--- Building wheel ---"
rm -rf dist/
# --no-isolation: use the setuptools/wheel already installed via
# requirements-build.txt rather than creating a fresh venv that
# downloads from PyPI (which can time out and bypasses hash verification).
python3 -m build --wheel --no-isolation --outdir dist/

echo "--- Verifying wheel installs and imports correctly ---"
# Uninstall editable install first and use -I (isolated mode) so Python does
# not import from the current working directory.
python3 -m pip uninstall -y antigravity-sdk-py || true
python3 -m pip install --force-reinstall --no-deps --no-index dist/*.whl

python3 -I -c "from google.antigravity.agent import Agent; print('Import OK: Agent')"
python3 -I -c "from google.antigravity.connections.local_connection import LocalConnection; print('Import OK: LocalConnection')"

echo "--- Presubmit passed ---"
