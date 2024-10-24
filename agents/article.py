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

base_dir = Path(__file__).parent

def load_artifacts(styleguide_path: Path) -> list:
    with open(styleguide_path, 'r') as s:
        return json.load(s)

class EvaluationResult(BaseModel):
    sections: Any

class ArticleEvaluator(Workflow):
    
    def run(self, article, requirements) -> Iterator[RunResponse]:

        reviews = []
        
        for group, reqs in requirements["groups"].items():            
            # Loop over each section in the article
            for section in article:
                section_title = section["title"]
                section_review_path = score_dir.joinpath(f"{group}_{section_title}.json")
                reviews.append(str(section_review_path))
                
                criteria_agent: Agent = Agent(
                    model=OpenAIChat(id='gpt-4o', max_tokens=7000),
                    add_references_to_prompt=True,
                    instructions=f"""
                        Task: Establish Grading Criteria for each section of the article based on the given requirements. Your output will be passed to Agent 2 for further evaluation.

                        <article section>
                        {json.dumps(section)}
                        </article secion>

                        <requirements>
                        {json.dumps(reqs)}
                        </requirements>

                        Content Section Evaluation Framework
                        
                        **NOTE**: If the content of the SECTION is EMPTY, there is no need to evaluate it. DO NOT EVALUATE.

                        Initial Assessment Phase
                        1. Section-by-Section Evaluation:
                        - Identify Applicable Requirements:
                            - For each section of the article in order, evaluate which requirements are applicable.
                            - Document the reasoning for including or excluding each requirement.
                        - Proceed with Grading:
                            - Only grade the requirements that are applicable to the section.

                        Grading Scale Definition
                        - 0.0: No adherence to the requirement.
                        - 0.25: Minimal adherence with significant gaps.
                        - 0.5: Partial adherence with notable room for improvement.
                        - 0.75: Strong adherence with minor improvements possible.
                        - 1.0: Complete adherence to the requirement.

                        Evaluation Process (Per Section)
                        **NOTE** The hierarchy of the section is specified under the 'hierarchy' key. 
                        1. Applicability Assessment:
                        - Review Requirements:
                            - Assess each requirement against the purpose of the section.
                            - Determine if the requirement is relevant.
                        - Document Relevance:
                            - Clearly state why each requirement is or isn't applicable.
                            - Highlight any edge cases or unclear applicability.

                        2. Content Mapping:
                        - Map Requirements to Content:
                            - Link each applicable requirement to specific parts of the section's content.
                        - Identify Gaps:
                            - Note any missing or incomplete mappings.
                        - Detect Overlaps:
                            - Identify any content overlap with other sections.

                        3. Detailed Evaluation:
                        - Score Assignment:
                            - For each applicable requirement, assign a score based on the grading scale.
                            - IF APPLICABLE = True: 
                            **DO NOT ASSIGN NULL TO ANYTHING. THE ONLY ACCEPTABLE SCORE IS 0-1.**
                            - IF NOT APPLICABLE DO NOT GRADE IT.
                        - Provide Evidence:
                            - Offer specific examples or evidence from the content that support the assigned score.
                        - Reasoning:
                            - Explain the rationale behind each score.
                        - Confidence Rating:
                            - Assign a confidence level (0 to 1) indicating how certain you are that the content meets the requirement.
                        - Special Considerations:
                            - Note any unique factors influencing the evaluation.

                        Key Principles
                        - Applicability First: Always assess applicability before grading.
                        - Use the Full Sliding Scale: Avoid binary scoring; utilize the entire range for nuanced evaluation.
                        - Specific Evidence: Provide concrete examples for all scores.
                        - Clear Reasoning: Ensure that reasoning is transparent and easy to follow.
                        - Context Awareness: Consider the context of each section during evaluation.
                        - Meaningful Overlaps: Recognize and document significant overlaps without penalizing justified repetitions.

                        ---

                        Additional Evaluation Guidelines

                        1. Grading Scale Refinement:
                        - Emphasize the sliding nature of the grading scale to capture varying degrees of adherence.
                        2. Content Complexity and Clarity:
                        - Reflect on whether the content not only meets the requirement but also maintains clarity and quality as per the style guide.
                        3. Mapping and Observations:
                        - For each section, map requirements to content meticulously.
                        - Provide detailed observations and reasoning for each grade to ensure transparency and justification.
                        4. Handling Overlaps and Redundancies:
                        - When overlapping information exists (e.g., between an infobox and section text), assess whether the repetition serves a meaningful purpose or if it is redundant.
                        5. Thought Process Documentation:
                        - Clearly document your analytical process, observations, and key details for each section to maintain a comprehensive evaluation record.

                        Output Format

                        Your evaluation should be saved in the following structured JSON format:

                        {{
                        "sections": [
                            {{
                            "title": "Section Title",
                            "requirement_evaluations": [
                                {{
                                "requirement_id": "R1",
                                "applicable": true,
                                "applicability_reasoning": "Applicable because the lead section defines the article scope.",
                                "score": 1.0,
                                "confidence": 0.95,
                                "evidence": "The lead starts with a clear definition of the protein.",
                                "reasoning": "The section fully meets the requirement by providing a comprehensive definition.",
                                "overlap_notes": "No significant overlaps detected."
                                }},
                                {{
                                "requirement_id": "R7",
                                "applicable": true,
                                "applicability_reasoning": "Relevant to content sections to avoid redundancy.",
                                "score": 0.5,
                                "confidence": 0.80,
                                "evidence": "Information about gene location is repeated in both infobox and content.",
                                "reasoning": "Partial adherence; repetition is somewhat justified but could be streamlined.",
                                "overlap_notes": "Overlap with infobox data noted."
                                }}
                            ],
                            "meta_notes": "The section is well-defined but could improve by minimizing redundant information."
                            }},
                            {{
                            "title": "Another Section Title",
                            "requirement_evaluations": [
                                {{
                                "requirement_id": "R2",
                                "applicable": true,
                                "applicability_reasoning": "Relevant for language usage throughout the article.",
                                "score": 0.75,
                                "confidence": 0.90,
                                "evidence": "Gene names are correctly capitalized in most instances.",
                                "reasoning": "Strong adherence with minor inconsistencies in a few gene names.",
                                "overlap_notes": "No overlaps in this section."
                                }}
                            ],
                            "meta_notes": "Language usage is mostly consistent, enhancing clarity and adherence to guidelines."
                            }}
                        ]
                        }}
                        """.strip().splitlines(),
                    tools=[FileTools(base_dir=base_dir)],
                    save_response_to_file=str(section_review_path),
                    response_model=EvaluationResult
                )

                logger.info("Agent: Performing initial evaluation of article against requirements.")
                mapping: RunResponse = criteria_agent.run()
                if not mapping or not mapping.content:
                    yield RunResponse(run_id=self.run_id, content=f"Error: Agent failed.")
                
                print(reviews)

# Run the workflow
if __name__ == "__main__":
    # Define directories for evaluation and results
    requirements = load_artifacts(base_dir.joinpath("requirements.json"))
    article = load_artifacts(base_dir.joinpath("article.json"))
    score_dir = base_dir.joinpath("score/results_sj")

    if score_dir.is_dir():
        rmtree(path=score_dir, ignore_errors=True)
    score_dir.mkdir(parents=True, exist_ok=True)
    
    report: Iterator[RunResponse] = ArticleEvaluator(debug_mode=False).run(article, )
    pprint_run_response(report, markdown=True, show_time=True)
