# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

Please report (suspected) security vulnerabilities to **[security@example.com](mailto:security@example.com)**. You will receive a response within 48 hours. If the issue is confirmed, we will release a patch as soon as possible depending on complexity but historically within a few days.

## Security Best Practices

When using KTree:

- **Never commit kubeconfig files** to version control
- **Use least-privilege access** - KTree uses your current kubeconfig context
- **Review Kubernetes RBAC** - Ensure your kubeconfig has appropriate permissions
- **Keep dependencies updated** - We use Dependabot to track security updates

## Known Security Considerations

- KTree reads from your local `~/.kube/config` file
- KTree makes API calls to your Kubernetes cluster using your current context
- No credentials are stored by KTree - all authentication is handled by the Kubernetes client library

