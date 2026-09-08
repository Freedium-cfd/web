"""Tests for the non-article domain denylist matcher.

These exercise the pure matcher against the seed list — no Mongo needed.
"""
from freedium_library.api.blocked_domains import _SEED_DOMAINS, _matches

SEED = frozenset(_SEED_DOMAINS)


def _blocked(url: str) -> bool:
    return _matches(url, SEED)


def test_blocks_exact_and_subdomains():
    assert _blocked("https://youtube.com/watch?v=x")
    assert _blocked("https://www.youtube.com/watch?v=x")
    assert _blocked("https://m.youtube.com/watch?v=x")
    assert _blocked("https://x.com/user/status/1")
    # suffix rule: google.com blocks every subdomain
    assert _blocked("https://mail.google.com/")
    assert _blocked("https://docs.google.com/document/d/abc")
    assert _blocked("https://google.com/search?q=x")


def test_blocks_newly_added_domains():
    assert _blocked("https://quora.com/q")
    assert _blocked("https://bsky.app/profile/x")
    assert _blocked("https://temu.com/x")
    assert _blocked("https://huggingface.co/models")
    assert _blocked("https://disneyplus.com/")
    # unsupported publications
    assert _blocked("https://www.wsj.com/articles/some-article-12345678")
    assert _blocked("https://wsj.com/articles/foo")
    assert _blocked("https://astralcodexten.substack.com/p/some-post")
    assert _blocked("https://substack.com/home")
    assert _blocked("https://www.wired.com/story/europe-ai")
    assert _blocked("https://wired.com/story/test")


def test_blocks_collapsed_slash_form():
    # SvelteKit collapses // -> / in the path it forwards as render content.
    assert _blocked("https:/youtube.com/watch?v=x")
    assert _blocked("https:/x.com/user")


def test_blocks_bare_host():
    assert _blocked("youtube.com/watch?v=x")


def test_does_not_block_articles_or_ids():
    assert not _blocked("https://medium.com/@u/some-article-c636de890607")
    assert not _blocked("https:/medium.com/cloud-security/foo-c636de890607")
    assert not _blocked("https://the-ken.com/tradetricks/foo/")
    # a bare Medium post id has no host -> never blocked
    assert not _blocked("c636de890607")
    assert not _blocked("")


def test_does_not_block_lookalike_suffix():
    assert not _blocked("https://notyoutube.com/x")
    assert not _blocked("https://youtube.com.evil.test/x")


def test_seed_has_at_least_90_domains():
    # migrated originals (~40) + 50 more
    assert len(SEED) >= 90
