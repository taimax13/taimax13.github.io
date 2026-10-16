"""Validate the rendered portfolio without third-party Python dependencies."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.ids = []
        self.json_scripts = []
        self.json_content = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.json_content = ''

    def handle_data(self, data):
        if self.json_content is not None:
            self.json_content += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.json_content is not None:
            self.json_scripts.append(json.loads(self.json_content))
            self.json_content = None


def validate(directory):
    root = Path(directory).resolve()
    routes = {'/': 'index.html', '/chagu/': 'chagu/index.html',
              '/cover-letter/': 'cover-letter/index.html',
              '/projects-extended-info/': 'projects-extended-info/index.html',
              '/print': 'print.html'}
    pages = {}
    for route, filename in routes.items():
        text = (root / filename).read_text()
        assert not re.search(r'{{|{%|10\+ years|Global Talent visa|reverse propagation|\bTRR\b|\binventor\b', text, re.I), filename
        page = pages[route] = Page(text)
        assert len(page.ids) == len(set(page.ids)), f'Duplicate IDs: {route}'
        assert len([t for t, _ in page.elements if t == 'h1']) == 1, route
        assert any(t == 'html' and a.get('lang') == 'en' for t, a in page.elements), route
        assert any(t == 'meta' and a.get('name') == 'viewport' for t, a in page.elements), route
        assert any(t == 'meta' and a.get('name') == 'description' and a.get('content') for t, a in page.elements), route
        assert any(t == 'link' and a.get('rel') == 'canonical' and a.get('href') == 'https://taimax13.github.io' + route for t, a in page.elements), route
        assert page.json_scripts and page.json_scripts[0]['@type'] == 'Person', route
        assert all('alt' in a and a['alt'].strip() for t, a in page.elements if t == 'img'), route
        if route != '/print':
            assert any(t == 'main' and a.get('id') == 'main' for t, a in page.elements), route
            assert any(t == 'a' and a.get('href') == '#main' for t, a in page.elements), route
            assert any(t == 'meta' and a.get('property') == 'og:image' and a.get('content', '').endswith('talex-portrait-gold-teal-v2.png') for t, a in page.elements), route
    references = 0
    for route, page in pages.items():
        for tag, attrs in page.elements:
            assert not (tag == 'a' and attrs.get('target') == '_blank' and 'noopener' not in attrs.get('rel', '')), (route, attrs)
            value = attrs.get('src') if tag in {'img', 'script'} else attrs.get('href') if tag in {'a', 'link'} else None
            if not value:
                continue
            url = urlsplit(value)
            if url.scheme in {'mailto', 'tel', 'data'} or (url.netloc and url.netloc != 'taimax13.github.io'):
                continue
            path = unquote(url.path) or route
            if not path.startswith('/'):
                path = route.rsplit('/', 1)[0] + '/' + path
            filename = routes.get(path, path.lstrip('/') + ('index.html' if path.endswith('/') else ''))
            target = root / filename
            assert target.is_file(), f'Missing reference: {route} -> {value}'
            if url.fragment:
                target_page = pages.get(path) or Page(target.read_text())
                assert unquote(url.fragment) in target_page.ids, f'Missing anchor: {route} -> {value}'
            references += 1
    home = (root / 'index.html').read_text()
    for required in ['Creator, AI Data Scientist &amp; Researcher', 'August 2024',
                     'Dream team · Global corporation', 'Staff AI Engineer', '2025 — Present',
                     '2024 — End of 2025', '2022 — 2024', '2021 — 2022',
                     'PhD Researcher, Computer Science', 'Registered researcher',
                     'Advanced Data Science', 'Y-Data', 'Big Data Engineering',
                     'NAYA College', 'Specialist Diploma', 'MBA', 'Bologna',
                     'AI Performance Engineering Fellowship', 'Nebius Agentic AI Builder']:
        assert required in home, required
    for route, filename in routes.items():
        assert 'mailto:' not in (root / filename).read_text(), f'Public email link: {route}'
    assert 'Connect on LinkedIn' in home
    pdf_path = '/assets/files/talex-maxim-cv.pdf'
    pdf = (root / pdf_path.lstrip('/')).read_bytes()
    assert pdf.startswith(b'%PDF-') and len(pdf) > 1000, 'Missing or invalid downloadable CV'
    short_pdf_path = '/assets/files/talex-maxim-cv-short.pdf'
    assert (root / short_pdf_path.lstrip('/')).read_bytes().startswith(b'%PDF-'), 'Missing short CV'
    for route in ['/', '/print']:
        assert any(t == 'a' and a.get('href') == short_pdf_path and 'download' in a for t, a in pages[route].elements), f'Missing short CV download: {route}'
    print_cv = (root / 'print.html').read_text()
    for required in ['Security Beyond Chagu', 'SAST', 'SCA', 'YARA', 'Opengrep', 'Temporal', 'ATAS UK clearance.']:
        assert required in print_cv, f'Missing CV detail: {required}'
    for route in ['/', '/print']:
        assert any(t == 'a' and a.get('href') == pdf_path and 'download' in a for t, a in pages[route].elements), f'Missing CV download: {route}'
    assert not (root / 'CNAME').exists(), 'Template CNAME must not be deployed'
    assert not (root / 'vendor').exists(), 'Bundler dependencies must not be deployed'
    print(f'PASS: {len(routes)} routes, {references} internal links/assets, metadata, semantics, and required content.')


if __name__ == '__main__':
    validate(sys.argv[1] if len(sys.argv) > 1 else '_site')
