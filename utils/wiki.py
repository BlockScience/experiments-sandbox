import requests
import json
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import List
import wikitextparser as wtp
import mistune
from wikicrow import parse_wikicrow

class WikiSection:
    """
    Represents a section in a Wikipedia page.
    """
    def __init__(self, title: str, level: int, content: str):
        self.title = title
        self.level = level
        self.content = content
        
    def __repr__(self):
        return f"WikiSection(title='{self.title}', level={self.level}, type='{self.type}')"

class WikiPageParser:
    """
    A parser class to fetch and parse Wikipedia pages into structured sections.
    """

    WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self, url: str):
        """
        Initializes the parser with a Wikipedia page URL.

        :param url: The URL of the Wikipedia page to parse.
        """
        self.url = url
        self.page_title = self.extract_title_from_url(url)
        self.wikitext = self.fetch_wikitext()
        self.parsed = wtp.parse(self.wikitext)
        self.sections: List[WikiSection] = self.parse_sections()

    def extract_title_from_url(self, url: str) -> str:
        """
        Extracts the page title from a Wikipedia URL.

        :param url: The Wikipedia page URL.
        :return: The page title.
        """
        parsed_url = urlparse(url)
        if 'wikipedia.org' not in parsed_url.netloc:
            raise ValueError("URL must be a Wikipedia page.")
        path = parsed_url.path
        if path.startswith("/wiki/"):
            title = path[len("/wiki/"):]
            return unquote(title).replace('_', ' ')
        else:
            raise ValueError("Invalid Wikipedia page URL format.")

    def fetch_wikitext(self) -> str:
        """
        Fetches the wikitext of the Wikipedia page using the MediaWiki API.

        :return: The wikitext of the page.
        """
        params = {
            'action': 'query',
            'prop': 'revisions',
            'rvprop': 'content',
            'format': 'json',
            'titles': self.page_title,
            'formatversion': 2
        }
        try:
            response = requests.get(self.WIKIPEDIA_API_URL, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch wikitext: {e}")

        data = response.json()

        pages = data.get('query', {}).get('pages', [])
        if not pages:
            raise ValueError("Page not found.")
        page = pages[0]
        if 'missing' in page:
            raise ValueError("Page does not exist.")
        return page['revisions'][0]['content']

    def parse_sections(self) -> List[WikiSection]:
        """
        Parses the wikitext into sections.

        :return: A list of WikiSection objects.
        """
        sections = []
        all_sections = self.parsed.get_sections(include_subsections=True)

        for section in all_sections:
            title = section.title.strip() if section.title else "Introduction"
            level = section.level if section.title else 1  # Introduction has level 1
            content = section.contents.strip()
            sections.append(WikiSection(title, level, content))
        return sections

    def get_sections(self) -> List[WikiSection]:
        """
        Returns the list of parsed sections.

        :return: List of WikiSection objects.
        """
        return self.sections
    
    def extract_sections(self, parsed_html):
        sections = []
        current_section = None
        hierarchy = []
        
        # Split by <h1>, <h2>, or <h3> tags
        for line in parsed_html.splitlines():
            if line.startswith('<h1>') or line.startswith('<h2>') or line.startswith('<h3>'):
                if current_section:
                    sections.append(current_section)
                # Start a new section
                level = int(line[2])
                title = line.strip(f'<h{level}>').strip(f'</h{level}>').strip()
                
                # Update hierarchy
                hierarchy = hierarchy[:level-1] + [title]
                
                current_section = {
                    'title': title,
                    'content': '',
                    'hierarchy': ' > '.join(hierarchy)
                }
            elif current_section:
                # Accumulate content for the current section
                current_section['content'] += line + '\n'
        
        if current_section:
            sections.append(current_section)
        
        return sections

    def get_markdown_content(self) -> str:
        """
        Returns the parsed sections as a markdown-formatted string.

        :return: Markdown-formatted string of the parsed content.
        """
        content = [f"# {self.page_title}\n\n"]
        for section in self.sections:
            content.append(f"{'#' * section.level} {section.title}\n\n")
            content.append(f"{section.content}\n\n")
        return ''.join(content)

def save_to_json(data, output_path: str) -> None:
    """
    Saves the given data to a JSON file.

    :param data: The data to be saved as JSON.
    :param output_path: The path where the JSON file will be saved.
    """
    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=2, ensure_ascii=False)
        print(f"JSON file saved successfully at: {output_path}")
    except IOError as e:
        print(f"Error saving JSON file: {e}")

def process_wikipedia_url(url: str) -> None:
    """
    Processes a single Wikipedia URL, parses its content, and saves the sections as a JSON file.

    :param name: The name to use for the output file.
    :param url: The Wikipedia URL to process.
    """
    try:
        parser = WikiPageParser(url)
        markdown_content = parser.get_markdown_content()
        markdown = mistune.create_markdown()
        parsed = markdown(markdown_content)
        sections = parser.extract_sections(parsed)
        
        return sections

    except Exception as e:
        print(f"Error processing URL ({url}): {e}")


"""
TODO: 

Rewrite to be fetch && parse wikipedia link to JSON or MD
OR...
Rewrite to be a Wikipedia Tool, example below --

"""
if __name__ == "__main__":
    base_dir = Path(__file__).parent
    article = "https://en.wikipedia.org/wiki/ABCC11"
    styleguide = "https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Molecular_Biology/Style_guide_(gene_and_protein_articles)"
    output_path = Path(__file__).parent.parent
    print(output_path)
    # For wikicrow
    is_wikicrow = True
    protein = 'ABCC11'
    
    if is_wikicrow:
        wikicrow_path = str(output_path.joinpath(f"tmp/wikicrow/{protein}")) + '.txt'
        article = parse_wikicrow(wikicrow_path)
        save_to_json(article, f"{output_path}/article.json")
        styleguide = process_wikipedia_url(styleguide)
        save_to_json(styleguide, f"{output_path}/styleguide.json")
    else:
        process_wikipedia_url('article', article, output_path)

'''
import json
from typing import List, Optional

from phi.document import Document
from phi.knowledge.wikipedia import WikipediaKnowledgeBase
from phi.tools import Toolkit
from phi.utils.log import logger

class WikipediaTools(Toolkit):
    def __init__(self, knowledge_base: Optional[WikipediaKnowledgeBase] = None):
        super().__init__(name="wikipedia_tools")
        self.knowledge_base: Optional[WikipediaKnowledgeBase] = knowledge_base

        if self.knowledge_base is not None and isinstance(self.knowledge_base, WikipediaKnowledgeBase):
            self.register(self.search_wikipedia_and_update_knowledge_base)
        else:
            self.register(self.search_wikipedia)

    def search_wikipedia_and_update_knowledge_base(self, topic: str) -> str:
        """This function searches wikipedia for a topic, adds the results to the knowledge base and returns them.

        USE THIS FUNCTION TO GET INFORMATION WHICH DOES NOT EXIST.

        :param topic: The topic to search Wikipedia and add to knowledge base.
        :return: Relevant documents from Wikipedia knowledge base.
        """

        if self.knowledge_base is None:
            return "Knowledge base not provided"

        logger.debug(f"Adding to knowledge base: {topic}")
        self.knowledge_base.topics.append(topic)
        logger.debug("Loading knowledge base.")
        self.knowledge_base.load(recreate=False)
        logger.debug(f"Searching knowledge base: {topic}")
        relevant_docs: List[Document] = self.knowledge_base.search(query=topic)
        return json.dumps([doc.to_dict() for doc in relevant_docs])

    def search_wikipedia(self, query: str) -> str:
        """Searches Wikipedia for a query.

        :param query: The query to search for.
        :return: Relevant documents from wikipedia.
        """
        try:
            import wikipedia  # noqa: F401
        except ImportError:
            raise ImportError(
                "The `wikipedia` package is not installed. " "Please install it via `pip install wikipedia`."
            )

        logger.info(f"Searching wikipedia for: {query}")
        return json.dumps(Document(name=query, content=wikipedia.summary(query)).to_dict())
'''