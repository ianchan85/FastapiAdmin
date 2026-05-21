# Contributing to FastapiAdmin 🎉

Thank you for your interest in contributing! We welcome all forms of contributions — code, docs, bug reports, feature suggestions, and more.

## Quick Links

- 📖 **Full Contributing Guide**: [service.fastapiadmin.com/about/contributing](https://service.fastapiadmin.com/about/contributing)
- 🐛 **Report a Bug**: [GitHub Issues](https://github.com/fastapiadmin/FastapiAdmin/issues) | [Gitee Issues](https://gitee.com/fastapiadmin/FastapiAdmin/issues)
- 💡 **Feature Requests**: Open an Issue first to discuss before coding
- 📝 **Development Guidelines**: [Code Style Guide](https://service.fastapiadmin.com/guide/guidelines)
- 💬 **Community**: Join our WeChat group (QR code in [README](./README.md))

## Before You Start

1. Check existing [Issues](https://github.com/fastapiadmin/FastapiAdmin/issues) to avoid duplicates
2. For large changes, open an Issue first to align on the approach
3. Follow the [commit message convention](https://service.fastapiadmin.com/guide/guidelines)

## Local Development Setup

```bash
# Backend
cd backend && uv sync && uv run main.py run --env=dev

# Frontend
cd frontend/web && pnpm install && pnpm run dev

# Docs
cd frontend/docs && pnpm install && pnpm run dev
```

## Pull Request Process

1. Fork the repo and create a feature branch (`feature/xxx` or `bugfix/xxx`)
2. Make your changes and commit with conventional messages
3. Run lint checks: `ruff check` (backend) / `pnpm lint` (frontend)
4. Open a PR targeting the **`dev`** branch
5. Wait for review — we'll respond as soon as possible

## Contributor License Agreement

By contributing, you agree that your contributions will be licensed under the project's [MIT License](./LICENSE).

---

**Every contribution counts — from fixing a typo to building a new feature. Thank you! ❤️**
