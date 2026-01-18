# GitHub Repository Files

This directory contains GitHub-specific configuration files for the KTree project.

## Files Overview

### Workflows (`.github/workflows/`)
- **ci.yml** - Continuous Integration workflow that runs tests and linting on push/PR
- **release.yml** - Automated release workflow that builds binaries for all platforms when a tag is pushed

### Issue Templates (`.github/ISSUE_TEMPLATE/`)
- **bug_report.md** - Template for bug reports
- **feature_request.md** - Template for feature requests

### Other Files
- **pull_request_template.md** - Template for pull requests
- **dependabot.yml** - Configuration for automated dependency updates
- **SECURITY.md** - Security policy and vulnerability reporting
- **FUNDING.yml** - Sponsorship/funding configuration (update with your details)

## Setup Instructions

1. **Update URLs in pyproject.toml**: Replace `your-username` with your actual GitHub username
2. **Update SECURITY.md**: Replace `security@example.com` with your security contact email
3. **Update FUNDING.yml**: Add your funding/sponsorship links if applicable
4. **Update CHANGELOG.md**: Replace `your-username` with your actual GitHub username

## Workflow Features

### CI Workflow
- Runs on push to main/master/develop branches
- Runs on pull requests
- Tests on multiple Python versions (3.10, 3.11, 3.12, 3.13)
- Tests on Ubuntu and macOS
- Runs linting (ruff) and format checking (black)
- Runs test suite (pytest)
- Builds binaries for all platforms (Linux, macOS, Windows)

### Release Workflow
- Triggers on version tags (e.g., `v0.1.0`)
- Builds binaries for all platforms
- Creates release archives (tar.gz for Unix, zip for Windows)
- Uploads artifacts to GitHub Releases

## Customization

You can customize these workflows and templates to match your project's needs. Common customizations:

- Add more test environments
- Add code coverage reporting
- Add deployment steps
- Customize issue templates
- Add more workflow triggers

