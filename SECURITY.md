# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of `hatchling-autoextras-hook` seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:
- **Email**: durand.tibo+gh@gmail.com

### What to Include

Please include the following information in your report:
- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- We will acknowledge receipt of your vulnerability report within 3 business days
- We will send a more detailed response within 7 days indicating the next steps in handling your report
- We will keep you informed about the progress towards a fix and may ask for additional information or guidance

### Disclosure Policy

- We ask that you do not publicly disclose the issue until we have had a chance to address it
- Once a fix is available, we will:
  1. Release a patched version
  2. Publish a security advisory
  3. Credit you for the discovery (if you wish)

## Security Best Practices

When using `hatchling-autoextras-hook`:

1. **Keep Dependencies Updated**: Always use the latest version of the package to benefit from security patches
2. **Review Build Configuration**: Ensure your `pyproject.toml` configuration follows security best practices
3. **Audit Dependencies**: Regularly audit the dependencies listed in your project's extras
4. **Use Virtual Environments**: Always build packages in isolated virtual environments
5. **Verify Build Artifacts**: Check that generated wheels and source distributions contain only expected files

## Known Security Considerations

### Build-Time Execution

As a Hatchling metadata hook, this package runs during the build process. It has access to:
- Project metadata in `pyproject.toml`
- Optional dependencies configuration

The hook only reads project metadata and does not:
- Execute arbitrary code from project files
- Make network requests
- Write files outside the build context
- Access environment variables or system credentials

### Supply Chain Security

We recommend:
- Using pinned versions or version ranges for this package in your build dependencies
- Verifying package signatures when available
- Using tools like `pip-audit` to scan for known vulnerabilities

## Contact

For any security concerns or questions, please contact:
- **Email**: durand.tibo+gh@gmail.com

Thank you for helping keep `hatchling-autoextras-hook` and its users safe!
