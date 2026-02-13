"""
Tests for export_all pipeline.
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import responses

from yazio_exporter.client import YazioClient
from yazio_exporter.export_all import export_all, print_summary


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def mock_client():
    """Create a mock YazioClient."""
    client = YazioClient()
    client.set_token("mock_token")
    return client


def _patch_all_exports():
    """Return a stack of patches for all export functions used by export_all."""
    return [
        patch(
            "yazio_exporter.export_all.fetch_user",
            return_value={"id": 123, "name": "Test User", "email": "test@example.com"},
        ),
        patch(
            "yazio_exporter.export_all.auto_discover_months",
            return_value=["2024-01-15", "2024-01-20"],
        ),
        patch(
            "yazio_exporter.export_all.fetch_days_concurrent",
            return_value={
                "2024-01-15": {
                    "consumed": {
                        "products": [],
                        "recipe_portions": [],
                        "simple_products": [],
                    },
                    "goals": {"data": {}},
                },
                "2024-01-20": {
                    "consumed": {
                        "products": [],
                        "recipe_portions": [],
                        "simple_products": [],
                    },
                    "goals": {"data": {}},
                },
            },
        ),
        patch(
            "yazio_exporter.export_all.fetch_weight_range",
            return_value={"2024-01-15": 75.5, "2024-01-20": 75.3},
        ),
        patch(
            "yazio_exporter.export_all.fetch_all_nutrients",
            return_value={"vitamin.d": {"2024-01-15": 15.0, "2024-01-20": 18.0}},
        ),
        patch(
            "yazio_exporter.export_all.fetch_all_concurrent",
            return_value={"products": {}, "recipes": {}},
        ),
    ]


def test_export_all_creates_directory(temp_dir, mock_client):
    """Test that export_all creates the output directory."""
    output_dir = Path(temp_dir) / "my_data"

    patches = _patch_all_exports()
    for p in patches:
        p.start()
    try:
        export_all(mock_client, str(output_dir))
        assert output_dir.exists()
        assert output_dir.is_dir()
    finally:
        for p in patches:
            p.stop()


def test_export_all_creates_all_files(temp_dir, mock_client):
    """Test that export_all creates all expected files."""
    output_dir = Path(temp_dir) / "my_data"

    patches = _patch_all_exports()
    for p in patches:
        p.start()
    try:
        export_all(mock_client, str(output_dir))

        expected_files = [
            "profile.json",
            "days.json",
            "weight.json",
            "nutrients.json",
            "products.json",
            "summary.txt",
            "analysis.md",
            "llm_prompt.txt",
        ]

        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists(), f"{filename} should exist"
            assert file_path.is_file(), f"{filename} should be a file"
    finally:
        for p in patches:
            p.stop()


def test_export_all_files_have_content(temp_dir, mock_client):
    """Test that all exported files have content."""
    output_dir = Path(temp_dir) / "my_data"

    patches = _patch_all_exports()
    for p in patches:
        p.start()
    try:
        export_all(mock_client, str(output_dir))

        json_files = [
            "profile.json",
            "days.json",
            "weight.json",
            "nutrients.json",
            "products.json",
        ]
        for filename in json_files:
            file_path = output_dir / filename
            assert file_path.stat().st_size > 0, f"{filename} should not be empty"

            with open(file_path) as f:
                data = json.load(f)
                assert isinstance(data, dict), f"{filename} should contain a dict"

        # Check summary.txt has content
        summary_path = output_dir / "summary.txt"
        assert summary_path.stat().st_size > 0, "summary.txt should not be empty"
    finally:
        for p in patches:
            p.stop()


def test_export_all_profile_has_real_data(temp_dir, mock_client):
    """Test that export_all writes real profile data, not placeholder."""
    output_dir = Path(temp_dir) / "my_data"

    patches = _patch_all_exports()
    for p in patches:
        p.start()
    try:
        export_all(mock_client, str(output_dir))

        with open(output_dir / "profile.json") as f:
            profile = json.load(f)

        # Must NOT be the old placeholder data
        assert profile.get("user") != "demo_user"
        assert profile.get("email") != "demo@example.com"
        # Must contain real mock data
        assert profile.get("name") == "Test User"
    finally:
        for p in patches:
            p.stop()


def test_export_all_returns_stats(temp_dir, mock_client):
    """Test that export_all returns statistics."""
    output_dir = Path(temp_dir) / "my_data"

    patches = _patch_all_exports()
    for p in patches:
        p.start()
    try:
        stats = export_all(mock_client, str(output_dir))

        assert isinstance(stats, dict)
        assert "days_exported" in stats
        assert "products_exported" in stats
        assert "weight_entries" in stats
        assert "output_dir" in stats

        assert Path(stats["output_dir"]) == output_dir.absolute()
        assert stats["days_exported"] == 2
        assert stats["weight_entries"] == 2
    finally:
        for p in patches:
            p.stop()


def test_print_summary_output(capsys):
    """Test that print_summary produces correct output."""
    stats = {
        "days_exported": 10,
        "products_exported": 25,
        "weight_entries": 8,
        "output_dir": "/path/to/output",
    }

    print_summary(stats)

    captured = capsys.readouterr()
    output = captured.err  # print_summary writes to stderr

    assert "10 days exported" in output
    assert "25 products" in output
    assert "8 weight entries" in output
    assert "/path/to/output" in output


def test_export_all_creates_nested_directory(temp_dir, mock_client):
    """Test that export_all creates nested directories."""
    output_dir = Path(temp_dir) / "path" / "to" / "my_data"

    patches = _patch_all_exports()
    for p in patches:
        p.start()
    try:
        export_all(mock_client, str(output_dir))
        assert output_dir.exists()
        assert output_dir.is_dir()
    finally:
        for p in patches:
            p.stop()


def test_export_all_existing_directory(temp_dir, mock_client):
    """Test that export_all works with existing directory."""
    output_dir = Path(temp_dir) / "existing_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    patches = _patch_all_exports()
    for p in patches:
        p.start()
    try:
        export_all(mock_client, str(output_dir))
        assert output_dir.exists()
        assert (output_dir / "profile.json").exists()
    finally:
        for p in patches:
            p.stop()


@patch("yazio_exporter.export_all.fetch_all_concurrent")
@patch("yazio_exporter.export_all.fetch_all_nutrients")
@patch("yazio_exporter.export_all.fetch_weight_range")
@patch("yazio_exporter.export_all.fetch_days_concurrent")
@patch("yazio_exporter.export_all.auto_discover_months")
@patch("yazio_exporter.export_all.fetch_user")
@responses.activate
def test_export_all_runs_complete_pipeline(
    mock_fetch_user,
    mock_auto_discover,
    mock_fetch_days,
    mock_fetch_weight_range,
    mock_fetch_nutrients,
    mock_fetch_all_concurrent,
    temp_dir,
):
    """Test that export_all executes all pipeline steps."""
    mock_fetch_user.return_value = {"id": 123, "name": "Test User"}
    mock_auto_discover.return_value = ["2024-01-01", "2024-01-02"]
    mock_fetch_days.return_value = {
        "2024-01-01": {"consumed": {"products": [], "recipe_portions": [], "simple_products": []}},
        "2024-01-02": {"consumed": {"products": [], "recipe_portions": [], "simple_products": []}},
    }
    mock_fetch_weight_range.return_value = {"2024-01-01": 75.5, "2024-01-02": 75.3}
    mock_fetch_nutrients.return_value = {"vitamin.d": {"2024-01-01": 15.0}}
    mock_fetch_all_concurrent.return_value = {"products": {}, "recipes": {}}

    # Mock login endpoint
    responses.add(
        responses.POST,
        "https://yzapi.yazio.com/v15/oauth/token",
        json={"access_token": "test_token_12345"},
        status=200,
    )

    # Create client and authenticate
    from yazio_exporter.auth import login

    token = login("test@example.com", "testpassword")
    assert token == "test_token_12345"

    client = YazioClient()
    client.set_token(token)
    output_dir = Path(temp_dir) / "pipeline_test"

    stats = export_all(client, str(output_dir))

    # Verify all export functions were called
    mock_fetch_user.assert_called_once_with(client)
    assert mock_auto_discover.called
    assert mock_fetch_days.called
    assert mock_fetch_weight_range.called
    assert mock_fetch_nutrients.called
    assert mock_fetch_all_concurrent.called

    # Verify stats were generated
    assert isinstance(stats, dict)
    assert stats["days_exported"] == 2
    assert stats["weight_entries"] == 2

    # Verify output directory was created
    assert output_dir.exists()
