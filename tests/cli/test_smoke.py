from click.testing import CliRunner

from open_waterfall.cli.app import main


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Open Waterfall CLI" in result.output

