# Security policy

## What this site is

`circulartextilealliance.org` is a **static** site: hand-authored HTML, CSS and a
single progressive-enhancement script, served by GitHub Pages. There is no
backend, no database, no authentication, no session state and no user accounts.
No personal data is collected, stored or processed by the site itself.

## Third-party requests

Exactly one third-party origin is contacted by a visitor's browser:

| Origin | What for | Why it is there |
| :-- | :-- | :-- |
| `images.unsplash.com` | The hero photograph and the eight card images | Carried over from the source design; see README for how to vendor these locally instead |

Fonts are self-hosted, so no request reaches Google Fonts or any other font CDN.
There is no analytics, no tag manager, no tracking pixel and no cookie of any
kind — the site sets none and needs no consent banner.

A Content-Security-Policy is declared in the page head. It permits no inline
styles or scripts and no origins other than the site itself and the image host
above. A CSP delivered as a response header is stronger than one in a `<meta>`
tag; if this site later moves behind a CDN or a host that can set headers,
promote it (and add `frame-ancestors`, which a meta-delivered CSP ignores).

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

Out of scope: the security posture of `images.unsplash.com`, and vulnerabilities
that require a compromised GitHub account or a modified local clone.
