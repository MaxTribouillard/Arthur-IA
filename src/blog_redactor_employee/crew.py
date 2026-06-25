import os
import json
from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
	SerperDevTool
)


from pydantic import BaseModel
from jambo import SchemaConverter

gemini = LLM(
    model="openrouter/meta-llama/llama-3.1-70b-instruct"
)

@CrewBase
class BlogRedactorEmployeeCrew:
    """BlogRedactorEmployee crew"""

    
    @agent
    def redacteur_web_expert_seo(self) -> Agent:
        
        
        return Agent(
            config=self.agents_config["redacteur_web_expert_seo"],
            
            
            tools=[				SerperDevTool(search_url="macron")],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=gemini
            
        )
        
    
    @agent
    def redacteur_en_chef_et_responsable_qualite(self) -> Agent:
        
        
        return Agent(
            config=self.agents_config["redacteur_en_chef_et_responsable_qualite"],
            
            
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            
            max_execution_time=None,
            llm=gemini
            
        )
        
    

    
    @task
    def recherche_et_redaction(self) -> Task:
        return Task(
            config=self.tasks_config["recherche_et_redaction"],
            markdown=False,
            output_json=self._load_response_format("recherche_et_redaction"),
            
        )
    
    @task
    def revue_et_publication(self) -> Task:
        return Task(
            config=self.tasks_config["revue_et_publication"],
            markdown=False,
            
            
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the BlogRedactorEmployee crew"""

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,

            chat_llm=gemini,
        )


    def _load_response_format(self, name):
        with open(os.path.join(self.base_directory, "config", f"{name}.json")) as f:
            json_schema = json.loads(f.read())

        return SchemaConverter.build(json_schema)

