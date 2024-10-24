import json
from phi.model.openai import OpenAIChat
from pathlib import Path
from phi.tools.file import FileTools
from typing import Iterator
from shutil import rmtree
from pydantic import BaseModel
from typing import Any

from phi.agent import Agent, RunResponse
from phi.workflow import Workflow
from phi.utils.pprint import pprint_run_response
from phi.utils.log import logger


# Define directories for evaluation and results
base_dir = Path(__file__).parent

class StyleGuideRequirements(BaseModel):
    groups: Any

def load_styleguide(styleguide_path: Path) -> list:
    with open(styleguide_path, 'r') as s:
        return json.load(s)

def prepare_output_directory(output_path: Path):
    if output_path.is_dir():
        rmtree(path=output_path, ignore_errors=True)
    output_path.mkdir(parents=True, exist_ok=True)

class StyleGuideParser(Workflow):
    
    def run(self, output_path, styleguide) -> Iterator[RunResponse]:
        for index, section in enumerate(styleguide):
            output_file_path = str(output_path.joinpath(f"reqs_{index}.json"))
            agent = Agent(
                model=OpenAIChat(id='gpt-4o', max_tokens=10000, temperature="0.2"),
                add_references_to_prompt=True,
                save_response_to_file=output_file_path,
                response_model=StyleGuideRequirements,
                description="As a specialist in reviewing Wikipedia articles, your task is to extract and document at least 30 requirements from the style guide.",
                instructions=f"""
            
                <STYLEGUIDE SECTION>
                {json.dumps(section)}
                </STYLEGUIDE SECTION>
                Your task is to extract all requirements from a given style guide and present them in a structured JSON format. Follow the steps below to ensure comprehensive and accurate extraction:

                1. **Thoroughly Review the Style Guide**: Carefully read the entire style guide to understand its scope, target audience, and specific guidelines.

                2. **Identify Sections and Subsections**: Break down the style guide into its main sections and any nested subsections to organize the extraction process.

                3. **Extract All Prescriptive Guidelines**:
                - **Locate Prescriptive Statements**: Find all statements that provide rules, guidelines, or recommended practices. Look for imperative language such as 'must', 'should', 'always', 'never', 'prefer', and 'avoid'.
                - **Capture Exact Wording**: For each prescriptive statement, note the exact phrasing used in the style guide.

                4. **Document Each Requirement in Detail**:
                - **Unique Identifier**: Assign a unique ID to each requirement in the format "R{id}" (e.g., R1, R2, etc.).
                - **Description**: Provide a concise summary of what the requirement entails.
                - **Reference**: Include the exact quote from the style guide that defines the requirement.
                - **Category**: Classify the requirement into a type such as "Content", "Formatting", "Language Usage", "Citations", "Infoboxes", or "Structure".
                
                5. **Classify Each Requirement**:
                - **Imperative Standards**: Non-negotiable requirements that must be included to ensure compliance.
                - **Best Practices**: Strongly recommended guidelines that may be adjusted based on context.
                - **Flexible Guidelines**: Optional guidelines that can be applied depending on the article's context.
                - **Contextual Considerations**: Requirements that apply under specific conditions (e.g., certain article types or content).
                - **Supplementary Information**: Additional, non-essential information that enhances the article.
                - **Non-Applicable Elements**: Requirements that do not apply to the current article or content.
                
                6. Review Each Requirement:
                - **Where**: Determine where the requirement should be applied within an article (lead section, content section, infobox, etc.).
                - **When**: Establish when the requirement should be applied, based on the article's specific content and context.

                7. **Organize Requirements into Groups**: Categorize the requirements under relevant groups based on their nature (e.g., Content, Formatting).

                8. **Format the Output as Structured JSON**:
                - **Structure**: The JSON should have a top-level key named "groups", with each group containing its relevant requirements.
                - **Requirement Object**: Each requirement should follow this structure:
                    ```json
                    {{
                        "id": "R{id}",
                        "description": "Brief description of the requirement",
                        "reference": "Exact quote from the style guide",
                        "category": "Requirement type",
                        "classification": "Imperative Standards",
                        "where": "Lead section",
                        "when": "Always applicable for gene/protein articles."
                    }}
                    ```

                9. **Ensure Completeness and Accuracy**: After extraction, review the JSON to confirm that all requirements from the style guide are included and correctly categorized.

                10. **Output Only the JSON**: The final response should contain only the JSON structure with all extracted requirements. Do not include any additional text or explanations.

                **Example Output**:
                {{
                    "groups": [
                        {{
                            "name": "Content",
                            "description": "Requirements related to the substantive content of the articles.",
                            "requirements": [
                                {{
                                    "id": "R1",
                                    "description": "An article should start with a clear definition in the lead section.",
                                    "reference": "The first sentence of the lead should define what the scope of the article is.",
                                    "category": "Content",
                                    "classification": "Imperative Standards",
                                    "where": "Lead section",
                                    "when": "Always applicable."
                                }},
                                ...
                            ]
                        }},
                        {{
                            "name": "Language Usage",
                            "description": "Guidelines for the appropriate use of language, including gene nomenclature and abbreviations.",
                            "requirements": [
                                {{
                                    "id": "R2",
                                    "description": "Human gene names should be written in all capitals.",
                                    "reference": "Human gene names are written in capitals, for example ALDOA, INS, etc.",
                                    "category": "Language Usage",
                                    "classification": "Imperative Standards",
                                    "where": "Throughout the article",
                                    "when": "Applicable for human genes only."
                                }},
                                ...
                            ]
                        }}
                    ]
                }}
                
                """.strip().splitlines(),
            )
            
            logger.info("Agent: Performing initial evaluation of article against requirements.")
            requirements: RunResponse = agent.run()
            if not requirements or not requirements.content:
                yield RunResponse(run_id=self.run_id, content=f"Error: Agent failed.")

if __name__ == "__main__":
    styleguide = load_styleguide(base_dir.joinpath("styleguide.json"))
    output_path = base_dir.joinpath("requirements")
    
    if output_path.is_dir():
        rmtree(path=output_path, ignore_errors=True)
    output_path.mkdir(parents=True, exist_ok=True)
    
    report: Iterator[RunResponse] = StyleGuideParser(debug_mode=False).run(output_path, styleguide)
    pprint_run_response(report, markdown=True, show_time=True)
