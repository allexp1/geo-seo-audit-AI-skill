"""Offline tests for the AgentReady v2.0 checklist in scripts/agent_readiness.py.

Run: python3 -m pytest -q tests
"""
import sys
from pathlib import Path

import pytest
from requests.structures import CaseInsensitiveDict

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import agent_readiness as ar  # noqa: E402

GOOD_HOME = """<!doctype html><html><head>
<link rel="ai-catalog" href="/.well-known/ai-catalog.json">
<link rel="alternate" type="text/markdown" href="/index.md">
<link rel="alternate" type="text/plain" href="/llms.txt">
<script type="application/ld+json">{"@type":"SoftwareApplication","name":"Acme"}</script>
<script>if (document.modelContext) document.modelContext.registerTool({name:"x"})</script>
</head><body><header><nav><a href="/docs">Docs</a><a href="/pricing">Pricing</a><a href="about.html">About</a></nav></header>
<main><h1>Acme</h1><p>""" + "word " * 150 + """ Plans from $10 a month.</p></main><footer><a href="/llms.txt">llms.txt</a></footer></body></html>"""


class Resp:
    def __init__(self, status=200, body="", ctype="text/html", headers=None, url="https://acme.test/"):
        self.status_code = status
        self.text = body
        self.url = url
        self.headers = CaseInsensitiveDict({"content-type": ctype, **(headers or {})})

    def iter_content(self, chunk_size=1024, decode_unicode=True):
        yield self.text

    def close(self):
        pass


def site(routes, home=GOOD_HOME, posts=None):
    """routes: path -> Resp; unknown paths fall back to a 404 page."""
    def fetch(url, ua, accept="*/*"):
        path = "/" + url.split("/", 3)[3] if url.count("/") >= 3 else "/"
        if path == "/" and "markdown" in accept and "/md" in routes:
            return routes["/md"]
        if path == "/":
            return Resp(200, home)
        return routes.get(path, Resp(404, "<!doctype html>not found"))

    class Post:
        @staticmethod
        def post(url, **kw):
            return (posts or {}).get("/" + url.split("/", 3)[3], Resp(404, "nope"))
    return fetch, Post


def run(monkeypatch, routes, home=GOOD_HOME, posts=None):
    fetch, post = site(routes, home, posts)
    monkeypatch.setattr(ar, "fetch", fetch)
    monkeypatch.setattr(ar, "requests", post)
    out = ar.analyze("https://acme.test/")
    return {c["id"]: c for c in out["agentready"]["checks"]}, out


GOOD_ROUTES = {
    "/robots.txt": Resp(200, "User-agent: *\nDisallow: /search/\nSitemap: https://acme.test/sitemap.xml\n", "text/plain"),
    "/sitemap.xml": Resp(200, "<urlset></urlset>", "application/xml"),
    "/llms.txt": Resp(200, "# Acme\n> docs", "text/plain"),
    "/.well-known/ai-catalog.json": Resp(200, '{"entries": []}', "application/json"),
    "/md": Resp(200, "# Acme", "text/markdown"),
}


def test_a_ready_site_passes_every_read_and_find_rule(monkeypatch):
    checks, out = run(monkeypatch, GOOD_ROUTES)
    for rid in ("AR-FIND-01", "AR-FIND-03", "AR-FIND-04", "AR-READ-01", "AR-READ-02", "AR-READ-03",
                "AR-READ-06", "AR-READ-07", "AR-READ-08", "AR-READ-09", "AR-READ-11", "AR-ACT-07"):
        assert checks[rid]["status"] == "pass", (rid, checks[rid])
    assert out["agentready"]["summary"]["must_failed"] == []
    assert out["categories"]["interaction_readiness"]["webmcp"] is True  # document.modelContext


def test_soft_404_fails_the_must(monkeypatch):
    routes = dict(GOOD_ROUTES)
    fetch, post = site(routes)

    def soft(url, ua, accept="*/*"):
        r = fetch(url, ua, accept)
        return Resp(200, GOOD_HOME) if r.status_code == 404 else r
    monkeypatch.setattr(ar, "fetch", soft)
    monkeypatch.setattr(ar, "requests", post)
    out = ar.analyze("https://acme.test/")
    checks = {c["id"]: c for c in out["agentready"]["checks"]}
    assert checks["AR-READ-02"]["status"] == "fail"
    assert "AR-READ-02" in out["agentready"]["summary"]["must_failed"]


def test_robots_blocking_an_ai_crawler_fails_find_01(monkeypatch):
    routes = dict(GOOD_ROUTES)
    routes["/robots.txt"] = Resp(200, "User-agent: GPTBot\nUser-agent: ClaudeBot\nDisallow: /\n\n"
                                      "User-agent: *\nAllow: /\n", "text/plain")
    checks, _ = run(monkeypatch, routes)
    assert checks["AR-FIND-01"]["status"] == "fail"
    assert "gptbot" in checks["AR-FIND-01"]["evidence"] and "claudebot" in checks["AR-FIND-01"]["evidence"]


def test_unlinked_llms_txt_fails_read_06_but_passes_read_07(monkeypatch):
    home = GOOD_HOME.replace('<link rel="alternate" type="text/plain" href="/llms.txt">', "") \
                    .replace('<a href="/llms.txt">llms.txt</a>', "")
    checks, out = run(monkeypatch, GOOD_ROUTES, home=home)
    assert checks["AR-READ-07"]["status"] == "pass"
    assert checks["AR-READ-06"]["status"] == "fail"
    assert any("nothing links to it" in r["text"] for r in out["recommendations"])


def test_free_alone_is_review_not_pass(monkeypatch):
    home = GOOD_HOME.replace(" Plans from $10 a month.", " It is free.").replace('<a href="/pricing">Pricing</a>', "")
    checks, _ = run(monkeypatch, GOOD_ROUTES, home=home)
    assert checks["AR-READ-11"]["status"] == "review"


def test_mcp_found_by_handshake_when_get_returns_docs(monkeypatch):
    routes = dict(GOOD_ROUTES)
    routes["/mcp"] = Resp(200, "---\ntitle: docs", "text/markdown")
    posts = {"/mcp": Resp(200, '{"jsonrpc":"2.0","id":1,"result":{"serverInfo":{}}}', "application/json")}
    checks, _ = run(monkeypatch, routes, posts=posts)
    assert checks["AR-ACT-03"]["status"] == "pass"
    assert checks["AR-ACT-10"]["status"] == "pass"


def test_oauth_gated_mcp_counts(monkeypatch):
    posts = {"/mcp": Resp(401, "", "application/json", {"WWW-Authenticate": 'Bearer resource_metadata="x"'})}
    checks, _ = run(monkeypatch, GOOD_ROUTES, posts=posts)
    assert checks["AR-ACT-03"]["status"] == "pass"


def test_honest_429_is_not_a_bot_wall(monkeypatch):
    fetch, post = site(GOOD_ROUTES)

    def throttled(url, ua, accept="*/*"):
        if ua == ar.BOT_UA and url.rstrip("/") == "https://acme.test":
            return Resp(429, "slow down", "text/plain", {"Retry-After": "30"})
        return fetch(url, ua, accept)
    monkeypatch.setattr(ar, "fetch", throttled)
    monkeypatch.setattr(ar, "requests", post)
    out = ar.analyze("https://acme.test/")
    assert out["categories"]["access"]["bot_wall_detected"] is False


def test_403_for_bots_is_a_wall(monkeypatch):
    fetch, post = site(GOOD_ROUTES)

    def walled(url, ua, accept="*/*"):
        if ua == ar.BOT_UA and url.rstrip("/") == "https://acme.test":
            return Resp(403, "Just a moment...", "text/html")
        return fetch(url, ua, accept)
    monkeypatch.setattr(ar, "fetch", walled)
    monkeypatch.setattr(ar, "requests", post)
    out = ar.analyze("https://acme.test/")
    checks = {c["id"]: c for c in out["agentready"]["checks"]}
    assert checks["AR-FIND-01"]["status"] == "fail"


@pytest.mark.parametrize("path_site", ["https://user.github.io/app/"])
def test_site_under_a_path_gets_the_custom_domain_advice(monkeypatch, path_site):
    fetch, post = site({})

    def at_path(url, ua, accept="*/*"):
        r = fetch(url, ua, accept)
        if url.rstrip("/") == path_site.rstrip("/"):
            r = Resp(200, GOOD_HOME, url=path_site)
        return r
    monkeypatch.setattr(ar, "fetch", at_path)
    monkeypatch.setattr(ar, "requests", post)
    out = ar.analyze(path_site)
    assert any("custom domain" in r["text"] for r in out["recommendations"])


def test_basic_auth_wall_is_not_an_mcp_server(monkeypatch):
    posts = {"/mcp": Resp(401, "login", "text/html", {"WWW-Authenticate": 'Basic realm="site"'})}
    checks, _ = run(monkeypatch, GOOD_ROUTES, posts=posts)
    assert checks["AR-ACT-03"]["status"] == "review"


def test_bearer_without_metadata_needs_the_protected_resource_document(monkeypatch):
    posts = {"/mcp": Resp(401, "", "application/json", {"WWW-Authenticate": "Bearer"})}
    checks, _ = run(monkeypatch, GOOD_ROUTES, posts=posts)
    assert checks["AR-ACT-03"]["status"] == "review"
    routes = dict(GOOD_ROUTES)
    routes["/.well-known/oauth-protected-resource"] = Resp(200, '{"resource":"x"}', "application/json")
    checks, _ = run(monkeypatch, routes, posts=posts)
    assert checks["AR-ACT-03"]["status"] == "pass"


def test_specific_allow_group_beats_wildcard_disallow(monkeypatch):
    routes = dict(GOOD_ROUTES)
    robots = "User-agent: *\nDisallow: /\n\n" + "".join(
        f"User-agent: {b}\n" for b in ("GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
                                       "Claude-SearchBot", "PerplexityBot", "Perplexity-User", "Google-Extended")
    ) + "Allow: /\n"
    routes["/robots.txt"] = Resp(200, robots, "text/plain")
    checks, _ = run(monkeypatch, routes)
    assert checks["AR-FIND-01"]["status"] == "pass", checks["AR-FIND-01"]


def test_wildcard_disallow_blocks_crawlers_without_their_own_group(monkeypatch):
    routes = dict(GOOD_ROUTES)
    routes["/robots.txt"] = Resp(200, "User-agent: *\nDisallow: /\n\nUser-agent: GPTBot\nAllow: /\n", "text/plain")
    checks, _ = run(monkeypatch, routes)
    assert checks["AR-FIND-01"]["status"] == "fail"
    assert "claudebot" in checks["AR-FIND-01"]["evidence"] and "gptbot" not in checks["AR-FIND-01"]["evidence"]


def test_ordinary_subpage_gets_no_custom_domain_advice(monkeypatch):
    fetch, post = site(GOOD_ROUTES)

    def sub(url, ua, accept="*/*"):
        r = fetch(url, ua, accept)
        if url.rstrip("/") == "https://acme.test/docs":
            r = Resp(200, GOOD_HOME, url="https://acme.test/docs/")
        return r
    monkeypatch.setattr(ar, "fetch", sub)
    monkeypatch.setattr(ar, "requests", post)
    out = ar.analyze("https://acme.test/docs/")
    assert not any("custom domain" in r["text"] for r in out["recommendations"])


def test_linked_llms_txt_under_a_path_counts(monkeypatch):
    home = GOOD_HOME.replace('href="/llms.txt"', 'href="llms.txt"')
    fetch, post = site({"/app/llms.txt": Resp(200, "# App", "text/plain")}, home=home)

    def at_path(url, ua, accept="*/*"):
        if url.rstrip("/") == "https://user.github.io/app":
            return Resp(200, home, url="https://user.github.io/app/")
        return fetch(url, ua, accept)
    monkeypatch.setattr(ar, "fetch", at_path)
    monkeypatch.setattr(ar, "requests", post)
    out = ar.analyze("https://user.github.io/app/")
    checks = {c["id"]: c for c in out["agentready"]["checks"]}
    assert checks["AR-READ-07"]["status"] == "pass"
    assert checks["AR-READ-06"]["status"] == "pass"


def test_subpage_does_not_fail_homepage_rules(monkeypatch):
    sub = "<html><head></head><body><main><p>" + "word " * 150 + "</p></main></body></html>"
    fetch, post = site(GOOD_ROUTES)

    def at_sub(url, ua, accept="*/*"):
        if url.rstrip("/") == "https://acme.test/docs/guide":
            return Resp(200, sub, url="https://acme.test/docs/guide")
        return fetch(url, ua, accept)
    monkeypatch.setattr(ar, "fetch", at_sub)
    monkeypatch.setattr(ar, "requests", post)
    out = ar.analyze("https://acme.test/docs/guide")
    checks = {c["id"]: c for c in out["agentready"]["checks"]}
    assert checks["AR-READ-08"]["status"] == "review"
    assert checks["AR-READ-03"]["status"] == "review"
    assert not any("AgentReady AR-READ-08" in r["text"] for r in out["recommendations"])


def test_soft_404_probe_stays_inside_a_path_hosted_app(monkeypatch):
    fetch, post = site(GOOD_ROUTES)
    probed = []

    def spa(url, ua, accept="*/*"):
        if url.startswith("https://user.github.io/app/"):
            probed.append(url)
            return Resp(200, GOOD_HOME, url=url)  # SPA shell for every /app/* route
        return fetch(url, ua, accept)
    monkeypatch.setattr(ar, "fetch", spa)
    monkeypatch.setattr(ar, "requests", post)
    out = ar.analyze("https://user.github.io/app/")
    checks = {c["id"]: c for c in out["agentready"]["checks"]}
    assert any("agentready-probe-" in u for u in probed)
    assert checks["AR-READ-02"]["status"] == "fail"


def test_pricing_link_must_lead_to_a_stated_price(monkeypatch):
    home = GOOD_HOME.replace(" Plans from $10 a month.", "")
    routes = dict(GOOD_ROUTES)
    checks, _ = run(monkeypatch, routes, home=home)  # /pricing is a 404 here
    assert checks["AR-READ-11"]["status"] == "review"
    routes["/pricing"] = Resp(200, "<html><body><p>Pro plan 12 USD a month</p></body></html>")
    checks, _ = run(monkeypatch, routes, home=home)
    assert checks["AR-READ-11"]["status"] == "pass"


def test_external_pricing_link_does_not_count(monkeypatch):
    home = GOOD_HOME.replace(" Plans from $10 a month.", "").replace(
        '<a href="/pricing">Pricing</a>', '<a href="https://blog.example/pricing">Pricing</a>')
    checks, _ = run(monkeypatch, GOOD_ROUTES, home=home)
    assert checks["AR-READ-11"]["status"] == "review"


@pytest.mark.parametrize("rule", ["Disallow: /*", "Disallow: /*$"])
def test_wildcard_whole_site_disallow_is_a_block(monkeypatch, rule):
    routes = dict(GOOD_ROUTES)
    routes["/robots.txt"] = Resp(200, f"User-agent: *\n{rule}\n", "text/plain")
    checks, _ = run(monkeypatch, routes)
    assert checks["AR-FIND-01"]["status"] == "fail"


class Stream(Resp):
    def __init__(self, chunks, **kw):
        super().__init__(200, "", "text/event-stream", **kw)
        self.chunks, self.closed = chunks, False

    def iter_content(self, chunk_size=1024, decode_unicode=True):
        yield from self.chunks

    def close(self):
        self.closed = True


def test_mcp_sse_reply_is_read_incrementally_and_closed(monkeypatch):
    def forever():
        yield "event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{}}\n\n"
        while True:
            yield ": keepalive\n\n"
    stream = Stream(forever())
    posts = {"/mcp": stream}
    checks, _ = run(monkeypatch, GOOD_ROUTES, posts=posts)
    assert checks["AR-ACT-03"]["status"] == "pass"
    assert stream.closed


def test_mcp_keepalives_without_a_result_stop_at_the_deadline(monkeypatch):
    def keepalives():
        while True:
            yield ": keepalive\n\n"
    monkeypatch.setattr(ar, "MCP_DEADLINE", 0.05)
    stream = Stream(keepalives())
    checks, _ = run(monkeypatch, GOOD_ROUTES, posts={"/mcp": stream})
    assert checks["AR-ACT-03"]["status"] == "review"
    assert stream.closed
