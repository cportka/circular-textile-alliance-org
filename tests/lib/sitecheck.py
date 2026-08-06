"""Shared helpers for the static site checks in tests/cases/.

Deliberately stdlib-only: CI runs `bash tests/run-tests.sh` on a bare runner, so
these must work with nothing installed beyond python3.
"""

import html.parser
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_failures = []
_checks = 0


def check(ok, message):
    """Record one assertion. Returns the boolean so callers can branch."""
    global _checks
    _checks += 1
    if not ok:
        _failures.append(message)
    return bool(ok)


def report(title):
    """Print a summary and exit non-zero if anything failed."""
    if _failures:
        print("  %s: %d/%d checks failed" % (title, len(_failures), _checks))
        for f in _failures:
            print("      - %s" % f)
        sys.exit(1)
    print("  %s: %d checks passed" % (title, _checks))
    sys.exit(0)


def read(relpath):
    with open(os.path.join(ROOT, relpath), encoding="utf-8") as fh:
        return fh.read()


def exists(relpath):
    return os.path.exists(os.path.join(ROOT, relpath))


class Element(object):
    __slots__ = ("tag", "attrs", "parent", "children", "text")

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children = []
        self.text = ""

    def get(self, name, default=None):
        return self.attrs.get(name, default)

    def classes(self):
        return (self.get("class") or "").split()

    def all_text(self):
        out = [self.text]
        for c in self.children:
            out.append(c.all_text())
        return " ".join(t for t in out if t).strip()

    def __repr__(self):
        return "<%s %s>" % (self.tag, self.attrs)


VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class _Parser(html.parser.HTMLParser):
    def __init__(self):
        html.parser.HTMLParser.__init__(self, convert_charrefs=True)
        self.root = Element("#document", {}, None)
        self.stack = [self.root]
        self.elements = []

    def handle_starttag(self, tag, attrs):
        el = Element(tag, {k: (v if v is not None else "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(el)
        self.elements.append(el)
        if tag not in VOID:
            self.stack.append(el)

    def handle_startendtag(self, tag, attrs):
        el = Element(tag, {k: (v if v is not None else "") for k, v in attrs}, self.stack[-1])
        self.stack[-1].children.append(el)
        self.elements.append(el)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].text += data


class Document(object):
    def __init__(self, relpath):
        self.path = relpath
        self.source = read(relpath)
        p = _Parser()
        p.feed(self.source)
        self.root = p.root
        self.elements = p.elements

    def find(self, tag=None, **attrs):
        out = []
        for el in self.elements:
            if tag and el.tag != tag:
                continue
            ok = True
            for k, v in attrs.items():
                key = k.rstrip("_").replace("_", "-")
                if el.get(key) != v:
                    ok = False
                    break
            if ok:
                out.append(el)
        return out

    def first(self, tag=None, **attrs):
        found = self.find(tag, **attrs)
        return found[0] if found else None

    def ids(self):
        return {el.get("id") for el in self.elements if el.get("id")}

    def meta(self, name=None, prop=None):
        for el in self.find("meta"):
            if name and el.get("name") == name:
                return el.get("content")
            if prop and el.get("property") == prop:
                return el.get("content")
        return None

    def local_refs(self):
        """(attribute value, source attribute) pairs pointing at repo-local files."""
        out = []
        for el in self.elements:
            for attr in ("href", "src"):
                val = el.get(attr)
                if not val:
                    continue
                if re.match(r"^(https?:|mailto:|tel:|data:|#|//)", val):
                    continue
                out.append((val.split("#")[0].split("?")[0], attr, el.tag))
        # url(...) references inside the stylesheet are resolved separately.
        return out
