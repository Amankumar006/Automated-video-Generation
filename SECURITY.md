# Security policy

Please do not report secrets, OAuth tokens, provider credentials, or private
production data in a public issue.

Report security problems privately to the repository owner through GitHub
security advisories or the maintainer's private contact channel. Include the
affected file or workflow, reproduction steps, impact, and any suggested
containment. Do not include live credentials in the report.

Local rules:

- Copy `.env.example` to `.env`; never commit `.env`.
- Keep YouTube, Instagram, X, LinkedIn, and model-provider tokens outside Git.
- Treat generated media and downloaded research bundles as disposable local
  state unless explicitly curated as a fixture.
- Review GitHub Actions permission changes before enabling publishing.
