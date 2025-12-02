"""Test that the web_search_agent package and its modules can be imported."""


class TestPackageLayout:
    """Test that the web_search_agent package and its modules can be imported."""

    def test_package_import(self):
        """Test that the web_search_agent package can be imported."""
        import web_search_agent

        assert web_search_agent is not None

    def test_config_module_import(self):
        """Test that the config module can be imported."""
        from web_search_agent import config

        assert config is not None

    def test_models_module_import(self):
        """Test that the models module can be imported."""
        from web_search_agent import models

        assert models is not None

    def test_tools_module_import(self):
        """Test that the tools module can be imported."""
        from web_search_agent import tools

        assert tools is not None

    def test_agent_module_import(self):
        """Test that the agent module can be imported."""
        from web_search_agent import agent

        assert agent is not None

    def test_mcp_server_module_import(self):
        """Test that the mcp_server module can be imported."""
        from web_search_agent import mcp_server

        assert mcp_server is not None

    def test_cli_module_import(self):
        """Test that the cli module can be imported."""
        from web_search_agent import cli

        assert cli is not None
