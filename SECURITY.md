# Security policy

## What this site is

`circulartextilealliance.org` is a **static** site: hand-authored HTML, CSS and a
single progressive-enhancement script, served by GitHub Pages. There is no
backend, no database, no authentication, no session state and no user accounts.
No personal data is collected, stored or processed by the site itself.

## Third-party requests

**None.** Every byte a visitor loads comes from this origin.

Fonts are self-hosted, so no request reaches Google Fonts or any other font CDN.
Photography is the alliance's own, served from `assets/img/photos/`. There is no
analytics, no tag manager, no tracking pixel and no cookie of any kind — the
site sets none and needs no consent banner.

`img-src` in the Content-Security-Policy is `'self' data:`, and the test suite
fails the build if a remote host reappears in either the markup or the policy,
so this cannot regress unnoticed.

A Content-Security-Policy is declared in the page head. It permits no inline
styles or scripts and no origin other than the site itself. A CSP delivered as a
response header is stronger than one in a `<meta>` tag; if this site later moves
behind a CDN or a host that can set headers, promote it (and add
`frame-ancestors`, which a meta-delivered CSP ignores).

## Reporting a vulnerability

Please report privately through GitHub Security Advisories:

**<https://github.com/cportka/circular-textile-alliance-org/security/advisories/new>**

Do not open a public issue for a security report. Expect an acknowledgement
within a few working days.

Machine-readable contact details are published at
[`/.well-known/security.txt`](./.well-known/security.txt) per RFC 9116.

## Scope

In scope: anything served from this repository — the markup, stylesheet, script,
fonts and images, and the GitHub Actions workflow that validates them.

Out of scope: vulnerabilities that require a compromised GitHub account or a
modified local clone.
