"""Cached, robots-respecting HTML ingestion of Dorar's inheritance subtree only."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

from lxml import html, etree
import requests

DATA_DIR = Path(__file__).resolve().parents[2] / 'data/fiqh/dorar_inheritance'
BASE = 'https://dorar.net'
SOURCE_ID = 'dorar_fiqhia'
SOURCE_NAME = 'الموسوعة الفقهية - الدرر السنية'
BOOK = 'كتاب المواريث'
AGENT = 'MAWARITH-AI-inheritance-ingestion/1.0 (educational archival; Kitab al-Mawarith only)'


def matching(text):
    return re.sub(r'[\u064b-\u065f\u0670\u0640]', '', text).strip()


def visible_label(node):
    node = deepcopy(node)
    for tip in node.xpath('.//span[contains(@class,"tip")]'):
        tip.drop_tree()
    return re.sub(r'\s+', ' ', node.text_content()).strip()


def article_url(url):
    parsed = urlsplit(urljoin(BASE, url))
    match = re.fullmatch(r'/feqhia/(\d+)(?:/[^/]+)?', parsed.path)
    if parsed.scheme != 'https' or parsed.netloc != 'dorar.net' or not match:
        raise ValueError('Only canonical Dorar fiqh article URLs are allowed')
    return BASE + '/feqhia/' + match[1]


def discover_tree(document):
    tree = html.fromstring(document)
    roots = [a.getparent() for a in tree.iter('a') if matching(visible_label(a)) == BOOK]
    if len(roots) != 1:
        raise ValueError('Cannot identify one inheritance navigation subtree')
    root = roots[0]
    directory, pages = {}, {}
    for a in root.iter('a'):
        label = visible_label(a)
        hierarchy = []
        for parent in reversed(list(a.iterancestors('li'))):
            links = parent.xpath('./a')
            if links:
                hierarchy.append(visible_label(links[0]))
        if not hierarchy or matching(hierarchy[0]) != BOOK:
            continue
        directory[matching(label).rstrip('.')] = hierarchy
        if re.fullmatch(r'/feqhia/\d+', a.get('href', '')):
            url = article_url(a.get('href'))
            pages[url] = {'canonical_url': url, 'page_title': label, 'hierarchy': hierarchy}
    return directory, pages


class CachedFetcher:
    def __init__(self, root=DATA_DIR, interval=1.05, session=None):
        self.raw = Path(root) / 'raw'
        self.raw.mkdir(parents=True, exist_ok=True)
        self.session = session or requests.Session()
        self.session.headers.update({'User-Agent': AGENT})
        self.interval = max(1.0, interval)
        self.last = 0.0
        self.robots = None

    def _get(self, url):
        time.sleep(max(0, self.interval - (time.monotonic() - self.last)))
        self.last = time.monotonic()
        response = self.session.get(url, timeout=40, allow_redirects=False)
        if response.status_code in {401, 403, 429}:
            raise PermissionError(f'Source access refused ({response.status_code}); ingestion stopped')
        response.raise_for_status()
        if response.is_redirect:
            target = urljoin(url, response.headers.get('Location', ''))
            if article_url(target) != article_url(url) or (self.robots and not self.robots.can_fetch(AGENT, target)):
                raise PermissionError('Redirect leaves approved article scope')
            # Follow one same-article title-slug redirect, with the same pacing.
            time.sleep(self.interval)
            self.last = time.monotonic()
            response = self.session.get(target, timeout=40, allow_redirects=False)
            if response.status_code in {401,403,429} or response.is_redirect:
                raise PermissionError('Canonical article access refused')
            response.raise_for_status()
        return response

    def check_policy(self):
        path = self.raw / 'robots.http.json'
        if path.exists():
            data = json.loads(path.read_text(encoding='utf-8'))
        else:
            response = self._get(BASE + '/robots.txt')
            data = {'url': response.url, 'text': response.text,
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                    'status_code': response.status_code, 'headers': dict(response.headers)}
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        parser = RobotFileParser(BASE + '/robots.txt')
        parser.parse(data['text'].splitlines())
        if not parser.can_fetch(AGENT, BASE + '/feqhia/13638'):
            raise PermissionError('robots.txt disallows inheritance ingestion')
        delay = parser.crawl_delay(AGENT) or parser.crawl_delay('*') or 0
        self.interval = max(self.interval, delay)
        self.robots = parser

    def fetch(self, entry):
        url = article_url(entry['canonical_url'])
        if self.robots is None or not self.robots.can_fetch(AGENT, url):
            raise PermissionError('Article access is not permitted by robots.txt')
        number = url.rsplit('/', 1)[-1]
        path = self.raw / f'{number}.html'
        meta_path = self.raw / f'{number}.http.json'
        if path.exists() and meta_path.exists():
            content = path.read_bytes()
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            if hashlib.sha256(content).hexdigest() != meta['sha256']:
                raise ValueError('Cached HTML hash mismatch')
        else:
            response = self._get(url)
            if 'text/html' not in response.headers.get('Content-Type', ''):
                raise ValueError('Unexpected non-HTML source response')
            content = response.content
            meta = {'url': response.url, 'fetched_at': datetime.now(timezone.utc).isoformat(),
                    'status_code': response.status_code, 'headers': dict(response.headers),
                    'sha256': hashlib.sha256(content).hexdigest()}
            path.write_bytes(content)
        meta.update(entry)
        if article_url(meta['url']) != url:
            raise ValueError('Cached source URL leaves approved article scope')
        declared = html.fromstring(content).xpath('//link[@rel="canonical"]/@href')
        canonical = urljoin(BASE, declared[0]) if declared else meta['url']
        if article_url(canonical) != url:
            raise ValueError('Declared canonical URL leaves approved article scope')
        meta['canonical_url'] = canonical
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
        return content, meta


def article_body(document, expected_title=None):
    tree = html.fromstring(document)
    areas = tree.xpath('//*[@id="cntnt"]')
    if len(areas) != 1:
        raise ValueError('Missing unambiguous article content container')
    area = areas[0]
    title_nodes = area.xpath('.//h1')
    title = visible_label(title_nodes[0]) if title_nodes else ''
    if expected_title and matching(title).rstrip('.') != matching(expected_title).rstrip('.'):
        raise ValueError('Article title does not match verified inheritance directory')
    bodies = area.xpath('./div[contains(concat(" ",normalize-space(@class)," ")," w-100 ")]')
    if len(bodies) != 1:
        raise ValueError('Unknown article markup; refusing to ingest navigation as content')
    return tree, deepcopy(bodies[0]), title


def content_kind(heading, text):
    h, t = matching(heading), matching(text)
    if 'تعريف' in h or 'معنى' in h or re.search(r'(?:^|\s)(?:اصطلاحا|الاصطلاح|هو|هي|هم)\s*[:：]?\s*(?:علم|من|الذين|نصيب|مال|المال|منع|زيادة|نقص|اقل)\b', t[:240]):
        return 'definition'
    if 'خلاف' in h or 'اختلف' in t or 'القول الاول' in t:
        return 'disagreement'
    if 'شرط' in h or 'شروط' in h:
        return 'condition'
    if 'مثال' in h or h.startswith('مسالة'):
        return 'example'
    if 'دليل' in h or 'ادلة' in h or 'الادلة' in h:
        return 'evidence'
    if 'حكم' in h or 'يرث' in t or 'نصيب' in t:
        return 'rule'
    return 'explanation'


def extract_chunks(document, meta):
    tree, body, title = article_body(document, meta['page_title'])
    has_visual = bool(body.xpath('.//img'))
    for node in body.xpath('.//script|.//style|.//a[@id="enc-tip"]|.//button'):
        node.drop_tree()
    # Preserve tooltip references inline with the precise claim they annotate.
    # Whitespace follows HTML display semantics; no words or citations rewritten.
    groups, heading, pieces = [], title, []
    def flush():
        nonlocal pieces
        text = re.sub(r'[ \t\r\f\v]+', ' ', ''.join(pieces))
        text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
        if text:
            groups.append((heading, text))
        pieces = []
    def walk(node):
        nonlocal heading
        if isinstance(node, etree._Comment):
            return
        classes = node.get('class', '').split()
        is_heading = node.tag in {'h2','h3','h4','h5','h6'} or any(re.fullmatch(r'title-\d+', c) for c in classes)
        if is_heading:
            flush()
            heading = re.sub(r'\s+', ' ', node.text_content()).strip()
            pieces.append(heading + '\n')
        elif node.tag == 'br':
            pieces.append('\n')
        else:
            if node.tag in {'p','div','li','blockquote','table','tr'}:
                pieces.append('\n')
            if node.text:
                pieces.append(node.text)
            for child in node:
                walk(child)
            if node.tag in {'p','div','li','blockquote','tr'}:
                pieces.append('\n')
        if node.tail:
            pieces.append(node.tail)
    walk(body)
    flush()
    # A leaf article is one topical ruling, with supporting subheadings.
    # Keep evidence, attributed disagreement and qualifications with that rule.
    # Split only at a named new topic, never at "الدليل"/"وجه الدلالة".
    bounded = []
    for label, text in groups:
        new_topic = re.match(r'^(?:تعريف|معنى|المبحث|المطلب|الفرع|المسالة)\b', matching(label))
        if not bounded or (new_topic and len(bounded[-1][1].split()) > 5):
            bounded.append((label, text))
        else:
            previous_label, previous_text = bounded[-1]
            bounded[-1] = (previous_label, previous_text + '\n' + text)
    groups = bounded
    chunks = []
    for index, (heading, text) in enumerate(groups):
        digest = hashlib.sha256(text.encode()).hexdigest()
        identity = f"{SOURCE_ID}:{meta['canonical_url']}:{meta['sha256']}:{index}:{digest}"
        hierarchy = meta['hierarchy']
        source = {'source_id': SOURCE_ID, 'source_name': SOURCE_NAME, 'source_type': 'fiqh_reference',
                  'book': BOOK, 'chapter': hierarchy[1] if len(hierarchy)>1 else None,
                  'section': hierarchy[2] if len(hierarchy)>2 else title, 'subsection': heading,
                  'topic': heading, 'page_title': title, 'canonical_url': meta['canonical_url'],
                  'source_url': meta['canonical_url'], 'publisher': 'الدرر السنية',
                  'verified_source': True, 'license_status': 'needs_review',
                  'content_kind': content_kind(heading, text), 'hierarchy': hierarchy,
                  'has_conditions': bool(re.search(r'اذا|بشرط|عند|الا|استثناء', matching(text))),
                  'has_school_qualification': bool(re.search(r'مذهب|المذاهب|الحنفية|المالكية|الشافعية|الحنابلة', matching(text))),
                  'has_example': bool(re.search(r'مثال|مثلا|مثل ان|نحو', matching(text))),
                  'has_unextracted_visual': has_visual,
                  'extraction_quality': 'clean_html', 'document_hash': meta['sha256'],
                  'document_sha256': meta['sha256'], 'excerpt_sha256': digest,
                  'chunk_id': hashlib.sha256(identity.encode()).hexdigest(),
                  'fetched_at': meta['fetched_at'], 'retrieval_eligible': len(text)<=7000}
        if source['content_kind']=='explanation' and any('شروط' in matching(part) for part in hierarchy):
            source['content_kind']='condition'
        chunks.append({'text': text, 'exact_text': text, 'source': source})
    related = []
    for link in tree.xpath('//*[@id="more-titles"]/following-sibling::ul[1]//a'):
        if link.get('href', '').startswith('/feqhia/'):
            related.append((article_url(link.get('href')), visible_label(link).rstrip('.')))
    return chunks, related


def ingest(root=DATA_DIR):
    root = Path(root)
    fetcher = CachedFetcher(root)
    fetcher.check_policy()
    navigation = root / 'raw/navigation.html'
    if not navigation.exists():
        # This is an index-only discovery request, not ingestion of other books.
        if not fetcher.robots.can_fetch(AGENT, BASE + '/feqhia'):
            raise PermissionError('robots.txt disallows navigation discovery')
        response = fetcher._get(BASE + '/feqhia')
        navigation.write_bytes(response.content)
    directory, pending = discover_tree(navigation.read_bytes())
    if BASE + '/feqhia/13638' not in pending:
        raise ValueError('Known inheritance seed missing from book navigation')
    processed = root / 'processed'
    processed.mkdir(parents=True, exist_ok=True)
    fetched, failed, skipped, chunks = [], [], [], []
    downloaded = 0
    queue = list(pending)
    seen = set(queue)
    while queue:
        url = queue.pop(0)
        entry = pending[url]
        try:
            document, meta = fetcher.fetch(entry)
            downloaded += 1
            page_chunks, links = extract_chunks(document, meta)
            chunks.extend(page_chunks)
            fetched.append(url)
            for linked, label in links:
                hierarchy = directory.get(matching(label).rstrip('.'))
                if hierarchy and linked not in seen:
                    seen.add(linked)
                    pending[linked] = {'canonical_url': linked, 'page_title': label, 'hierarchy': hierarchy}
                    queue.append(linked)
        except PermissionError:
            raise
        except ValueError as exc:
            if str(exc) == 'Missing unambiguous article content container':
                skipped.append({'url': url, 'reason': 'Inheritance navigation-only page; no article'})
            else:
                failed.append({'url': url, 'reason': str(exc)})
        except requests.RequestException as exc:
            failed.append({'url': url, 'reason': str(exc)})
        print(f'{len(fetched)} fetched; {len(queue)} queued; {url}', flush=True)
    report = {'discovered': len(pending), 'fetched': downloaded, 'article_pages': len(fetched),
              'failed': failed, 'skipped': skipped,
              'chunks': len(chunks), 'oversized_chunks': sum(not c['source']['retrieval_eligible'] for c in chunks)}
    (processed / 'chunks.json').write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding='utf-8')
    (processed / 'ingestion_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (processed / 'manifest.json').write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', action='store_true')
    args = parser.parse_args()
    report = ingest()
    if args.index:
        from backend.rag.dorar_retrieval import index_dorar
        report['indexed_points'] = index_dorar()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
