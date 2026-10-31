import asyncio
import datetime
from pathlib import Path
import pytest
from google.adk.agents import Agent
from google.adk.tools.skill_toolset import SkillToolset
from app.agent import root_agent, app, FerramentasDeArquivo, PLANOS_DIR, get_instruction


def test_root_agent_and_app_initialization():
    assert isinstance(root_agent, Agent)
    assert root_agent.name == "agente_estudos"
    assert app.name == "app"
    assert app.root_agent is root_agent


def test_instruction_contains_today_date():
    today = datetime.date.today().strftime("%Y-%m-%d")
    instruction = get_instruction()
    assert today in instruction
    assert "mentor" in instruction.lower()
    assert "plano-de-estudos" in instruction


def test_planos_directory_configured():
    assert PLANOS_DIR.is_dir()
    assert PLANOS_DIR.name == "planos"


@pytest.mark.asyncio
async def test_tools_configured():
    skill_toolset = None
    file_toolset = None
    for tool in root_agent.tools:
        if isinstance(tool, SkillToolset):
            skill_toolset = tool
        elif isinstance(tool, FerramentasDeArquivo):
            file_toolset = tool

    assert skill_toolset is not None, "SkillToolset deve estar registrado no agente"
    assert file_toolset is not None, "FerramentasDeArquivo deve estar registrado no agente"

    # Ferramentas de arquivo devem conter APENAS ReadFile e WriteFile
    tools = await file_toolset.get_tools()
    tool_names = [t.name for t in tools]
    assert sorted(tool_names) == ["ReadFile", "WriteFile"]

    # SkillToolset deve expor as ferramentas de skill
    skill_tools = await skill_toolset.get_tools()
    skill_tool_names = [t.name for t in skill_tools]
    assert "load_skill" in skill_tool_names
    assert "load_skill_resource" in skill_tool_names
