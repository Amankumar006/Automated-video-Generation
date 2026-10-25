from pipeline.source_asset_resolver import extract_official_image_candidates


def test_extracts_only_first_party_announcement_images():
    html = '''
    <meta property="og:image" content="https://kimi-img.kimi.ai/hero.webp">
    <meta property="og:image" content="https://unrelated.example/stock.jpg">
    <img src="/fallback.png">
    '''

    assert extract_official_image_candidates(html, "https://www.kimi.ai/blog/k3") == [
        "https://kimi-img.kimi.ai/hero.webp",
        "https://www.kimi.ai/fallback.png",
    ]
