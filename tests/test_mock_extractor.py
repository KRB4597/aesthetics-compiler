"""Mock extractor unit test — was 0% covered.

The mock extractor is the deterministic test-fixture tier; it isn't reached via
compile_document's auto-detected modes, so it is exercised directly here.
"""
from aesthetics_compiler.annotation.mock_extractor import MockExtractor


def test_mock_extractor_returns_populated_fixture():
    result = MockExtractor().extract()
    assert len(result.elements) >= 1
    for elem in result.elements:
        assert elem.aesthetic_vector is not None
        assert elem.id


def test_mock_extractor_is_deterministic():
    a = MockExtractor().extract()
    b = MockExtractor().extract()
    assert [e.id for e in a.elements] == [e.id for e in b.elements]
