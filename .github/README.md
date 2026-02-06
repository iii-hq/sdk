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
    Validate --> |on failure| Rollback[rollback.yml]
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
  Release --> BuildRust[Rust binary builds]
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
  - Builds Rust binaries for multiple platforms
  - Creates GitHub Release
  - Sends Slack notifications

- **[`validate-release.yml`](workflows/validate-release.yml)** - Validate release artifacts
  - **Trigger:** Automatically after release completes
  - Verifies published packages (npm, PyPI, crates.io) and binaries

- **[`rollback.yml`](workflows/rollback.yml)** - Rollback to a previous version
  - **Trigger:** Manual dispatch
  - **Inputs:** Target version and reason
  - Deletes problematic release and creates rollback tag

## Release Process

1. **Create Tag:** Run `create-tag.yml` workflow manually
   - Choose version bump type (patch/minor/major) or provide custom version
   - Workflow creates and pushes the tag

2. **Release:** `release.yml` automatically triggers on tag push
   - Tests all SDKs
   - Publishes packages
   - Builds binaries
   - Creates GitHub Release

3. **Validation:** `validate-release.yml` runs automatically
   - Verifies all artifacts were published correctly

4. **Rollback (if needed):** Run `rollback.yml` manually
   - Specify target version and reason
   - Deletes problematic release and tags