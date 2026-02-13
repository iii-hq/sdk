# CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration, testing, and releases.

## Architecture

```mermaid
flowchart TD
  subgraph ci [CI - Per Language on PR/Push]
    CINode[ci-node.yml]
    CIRust[ci-rust.yml]
    CIPython[ci-python.yml]
  end

  subgraph release [Release Flow]
    CreateTag[create-tag.yml\nManual Dispatch] --> |pushes v* tag| Release[release.yml]
    Release --> |on completion| Validate[validate-release.yml]
  end

  subgraph prerelease [Pre-release - Manual]
    PreNode[prerelease-node-sdk.yml]
    PrePython[prerelease-python-sdk.yml]
    PreRust[prerelease-rust-sdk.yml]
  end

  CINode --> |lint + type-check + test + build| DoneCI[Gate PRs]
  CIRust --> |fmt + clippy + test + build| DoneCI
  CIPython --> |ruff + mypy + pytest| DoneCI

  Release --> PublishNode[npm publish]
  Release --> PublishPython[PyPI publish]
  Release --> PublishRust[crates.io publish]
  Release --> GitHubRelease[GitHub Release]
```

## Workflows

### Continuous Integration

These workflows run automatically on pull requests and pushes to main:

- **[`ci-node.yml`](workflows/ci-node.yml)** - Node.js SDK CI
  - Linting, type checking, testing, and building
  - Runs on Node.js 20

- **[`ci-rust.yml`](workflows/ci-rust.yml)** - Rust SDK CI
  - Formatting (`cargo fmt`), linting (`cargo clippy`), testing, and building

- **[`ci-python.yml`](workflows/ci-python.yml)** - Python SDK CI
  - Linting (`ruff`), type checking (`mypy`), and testing (`pytest`)
  - Runs on Python 3.10, 3.11, and 3.12

### Pre-release Workflows

Manual workflows for publishing pre-release versions (alpha, beta, rc):

- **[`prerelease-node-sdk.yml`](workflows/prerelease-node-sdk.yml)** - Publish Node.js SDK pre-release to npm
- **[`prerelease-python-sdk.yml`](workflows/prerelease-python-sdk.yml)** - Publish Python SDK pre-release to PyPI
- **[`prerelease-rust-sdk.yml`](workflows/prerelease-rust-sdk.yml)** - Publish Rust SDK pre-release to crates.io

**How to trigger:** Go to Actions → Select workflow → Run workflow → Provide inputs:
- Pre-release label (e.g., `alpha`, `beta`, `rc`)
- Branch containing changes

### Release Workflows

- **[`create-tag.yml`](workflows/create-tag.yml)** - Create and push a version tag
  - **Trigger:** Manual dispatch
  - **Inputs:** Version bump type (patch/minor/major/custom)
  - Creates a `v*` tag which triggers the release workflow

- **[`release.yml`](workflows/release.yml)** - Full release process
  - **Trigger:** Automatically on push of `v*` tags
  - Runs tests for all languages
  - Publishes to npm, PyPI, and crates.io
  - Creates GitHub Release
  - Sends Slack notifications

- **[`validate-release.yml`](workflows/validate-release.yml)** - Validate release artifacts
  - **Trigger:** Automatically after release completes
  - Verifies published packages (npm, PyPI, crates.io)

- **[`rollback.yml`](workflows/rollback.yml)** - Rollback to a previous version
  - **Trigger:** Manual dispatch
  - **Inputs:** Target version and reason
  - Deletes problematic release and creates rollback tag

## Composite Actions

Reusable composite actions for setting up the III Engine in CI workflows:

### `setup-iii-engine`

Downloads, caches, and starts the III Engine server for integration tests.

**Inputs:**
- `engine-repo` (optional): GitHub repository containing III Engine releases (default: `{owner}/iii`)
- `engine-version` (optional): Engine version to download (default: `latest`)
- `config-path` (optional): Path to engine config YAML (default: `.github/engine-config/test-config.yml`)
- `github-token` (required): GitHub token for API access

**Outputs:**
- `engine-available`: `true` if engine is running, `false` if unavailable (graceful degradation)

**Usage:**
```yaml
- name: Setup III Engine
  id: engine
  uses: ./.github/actions/setup-iii-engine
  with:
    engine-repo: ${{ vars.ENGINE_REPO || '' }}
    engine-version: ${{ vars.ENGINE_VERSION || 'latest' }}
    github-token: ${{ github.token }}
```

The action automatically:
- Resolves the latest release tag if `engine-version` is `latest`
- Caches the binary to speed up subsequent runs
- Downloads the engine binary from GitHub releases
- Starts the engine server in the background
- Waits for health check (`http://localhost:3111/health`)
- Sets environment variables `III_BRIDGE_URL` and `III_HTTP_URL` are expected by tests

If the engine cannot be downloaded or started, the action outputs `engine-available=false` and does not fail the job. Tests should check this output and skip integration tests accordingly.

### `stop-iii-engine`

Stops the III Engine server and cleans up temporary files.

**No inputs required** - reads PID from `/tmp/iii-engine.pid`

**Usage:**
```yaml
- name: Stop III Engine
  if: always() && steps.engine.outputs.engine-available == 'true'
  uses: ./.github/actions/stop-iii-engine
```

Always use `if: always()` to ensure cleanup runs even if previous steps fail.

## Pre-commit Hooks

Pre-commit hooks automatically fix linting and formatting issues before commits, preventing fixable failures in CI.

### Setup

1. **Install pre-commit:**
   ```bash
   pip install pre-commit
   ```

2. **Install the git hooks:**
   ```bash
   pre-commit install
   ```

3. **Run on all files (optional, for initial setup):**
   ```bash
   pre-commit run --all-files
   ```

### Configured Hooks

- **Python**: Runs `ruff check --fix` and `mypy` on Python files
- **Node.js**: Runs `biome check --write` on TypeScript/JavaScript files
- **Rust**: Runs `cargo fmt --all` on Rust files
- **General**: Checks for trailing whitespace, end-of-file fixes, YAML validation, and large files

Hooks run automatically on `git commit` and only process staged files. To bypass (not recommended), use `git commit --no-verify`.

## Release Process

```mermaid
flowchart TD
  Start["Run create-tag.yml"] --> Inputs["Select: version_type + pre_release"]
  Inputs --> FetchStable["Get latest stable tag\n(filter out pre-release)"]
  FetchStable --> Bump["Apply bump\n(patch/minor/major)"]
  Bump --> CheckPre{pre_release?}
  CheckPre -->|none| StableVer["v0.1.1"]
  CheckPre -->|alpha| AlphaVer["v0.1.1-alpha"]
  CheckPre -->|beta| BetaVer["v0.1.1-beta"]
  CheckPre -->|rc| RcVer["v0.1.1-rc"]
  StableVer --> TagExists{Tag exists?}
  AlphaVer --> TagExists
  BetaVer --> TagExists
  RcVer --> TagExists
  TagExists -->|yes| Fail["Error: tag already exists"]
  TagExists -->|no| UpdateFiles["Update version files\nCommit + Tag + Push"]
  UpdateFiles --> Release["release.yml triggers"]
  Release --> DetectPre["Detect pre-release from tag"]
  DetectPre --> GHRelease["GitHub Release\n(prerelease flag set)"]
  DetectPre --> NpmPublish["npm publish --tag alpha/beta/rc/latest"]
  DetectPre --> PyPI["PyPI publish\n(auto-detected as pre-release)"]
  DetectPre --> Crates["crates.io publish\n(semver handles it)"]
```

1. **Create Tag:** Run `create-tag.yml` workflow manually
   - Choose version bump type (patch/minor/major) or provide custom version
   - Workflow creates and pushes the tag

2. **Release:** `release.yml` automatically triggers on tag push
   - Tests all SDKs
   - Publishes packages to npm, PyPI, crates.io
   - Creates GitHub Release

3. **Validation:** `validate-release.yml` runs automatically
   - Verifies packages are available on npm, PyPI, crates.io

4. **Rollback (if needed):** Run `rollback.yml` manually
   - Specify target version and reason
   - Deletes problematic release and tags
