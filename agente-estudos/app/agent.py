# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import Agent

from google.adk.apps import App
from google.adk.environment import LocalEnvironment
from google.adk.models import Gemini
from google.adk.skills import load_skill_from_dir
from google.adk.tools.environment import EnvironmentToolset
from google.adk.tools.skill_toolset import SkillDiscoveryMode, SkillToolset
from google.genai import types

# Lê o modelo da variável de ambiente MODEL com fallback para gemini-3.8-flash
MODEL = os.getenv("MODEL", "gemini-3.8-flash")

# Diretórios base resolvidos a partir deste arquivo
APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
PLANOS_DIR = PROJECT_DIR / "planos"
PLANOS_DIR.mkdir(parents=True, exist_ok=True)

# Carrega a skill de plano de estudos (L1 no catálogo e ferramentas L2/L3)
SKILL_DIR = APP_DIR / "skills" / "plano-de-estudos"
skill = load_skill_from_dir(SKILL_DIR)
skill_toolset = SkillToolset(
    skills=[skill],
    discovery_mode=SkillDiscoveryMode.EAGER,
    tool_filter=["load_skill", "load_skill_resource"],
)


# Subclasse de EnvironmentToolset expondo apenas ReadFile e WriteFile (sem shell)
class FerramentasDeArquivo(EnvironmentToolset):
    async def get_tools(self, readonly_context=None):
        tools = await super().get_tools(readonly_context)
        return [t for t in tools if t.name in ("ReadFile", "WriteFile")]


# Ambiente local isolado no diretório planos/ (working_dir como Path)
local_env = LocalEnvironment(working_dir=PLANOS_DIR)
file_toolset = FerramentasDeArquivo(environment=local_env)


# Instruction provider injetando dinamicamente a data atual
def get_instruction(context=None) -> str:
    hoje = datetime.date.today().strftime("%Y-%m-%d (%A)")
    return (
        f"Hoje é {hoje}.\n"
        "Você é um mentor especialista em organização e metodologia de estudos.\n"
        "Seu papel é orientar o estudante e montar planos de estudo personalizados e de alto impacto.\n"
        "Responda sempre em português do Brasil, em tom encorajador, direto e prático.\n"
        "Utilize a skill 'plano-de-estudos' para guiar todo o processo de planejamento, respeitando "
        "rigorosamente as regras de ativação (gating) e os passos de execução da skill."
    )


root_agent = Agent(
    # Keep in sync with create_params.root_agent_name in agents-cli-manifest.yaml:
    name="agente_estudos",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=get_instruction,
    tools=[skill_toolset, file_toolset],
)

app = App(
    root_agent=root_agent,
    name="app",
)
