from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
# Local imports
from .models import ResearchState, CompanyInfo, CompanyAnalysis
from .firecrawl import FirecrawlService
from .prompts import DeveloperToolsPrompts


class Workflow:
    
    def __init__(self):
        self.firecrawl = FirecrawlService()
        self.llm = ChatOpenAI(model = "gpt-4o-mini", temperature = 0.1)
        self.prompts = DeveloperToolsPrompts()
        self.workflow = self._build_workflow()


    def _build_workflow(self):
        pass
    
    # Set up langgraph
    # Create graph that agent flows through
    # Control state at which agent is at
    # First stage: extract various candidate tools 
    # Second stage: research particular tools
    # Third stage: analyze and recommend tools based on research findings
    
    
    # Create private methods
    
    # Step to extract tools from articles based on user query
    def _extract_tools_step(self, state: ResearchState) -> Dict[str, Any]:
        
        # Will use ResearchState from models and return a Dict full of candidate tools
        print(f"🕵🏽‍♂️ Finding articles about: {state.query}")
        
        article_query = f"{state.query} tools comparison best alternatives"
        # Search the article_query on the interet using Firecrawl method and return 3 results
        # These results will be in the form of urls
        search_results = self.firecrawl.search_companies(article_query, num_results=3)
        
        # All search results from firecrawl combined into 1 string to give to LLM for analysis of result tools for more info
        all_content = ""
        for result in search_results.data:
            # Get the URL from the result
            url = result.get("url", "")
            # Scrape each article using Firecrawl method
            scraped = self.firecrawl.scrape_company_pages(url)
            # If the scraping was successful, append the content to all_content
            if scraped:
                all_content += scraped.markdown[:1500] + "\n\n"
                
        # Pass content to LLM
        messages = [
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_SYSTEM),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query, all_content))
        ]
        
        # Get the response from the LLM
        # Parse out tools from response and update state
        try:
            response = self.llm.invoke(messages)
            tool_names = [
                name.strip()
                # Give tools on new lines
                for name in response.content.strip().split("\n")
                # Filter out empty lines (check if name exists)
                if name.strip()  
            ]
            print(f"🔧 Extracted tools: {','.join(tool_names[:5])}")
            # Setting extracted_tools in the state using langgraph
            return {"extracted_tools": tool_names}
        except Exception as e:
            print(f"Error during tool extraction: {e}")
            return {"extracted_tools": []}
        
    
    # Step to analyze each tool (helper method)
    def _analyze_step(self, company_name: str, content: str) -> CompanyAnalysis:
        
        # Use the LLM to analyze a specific company/tool based on its content
        structured_llm = self.llm.with_structured_output(CompanyAnalysis)
        
        # Prepare the messages for the LLM analysis
        messages = [
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(company_name, content))
        ]
        
        try:
            # Invoke the LLM with the messages to get structured analysis
            analysis = structured_llm.invoke(messages)
            return analysis
        except Exception as e:
            print(f"Error during analysis of {company_name}: {e}")
            # If analysis fails, return an empty CompanyAnalysis object to avoid crash
            return CompanyAnalysis(
                pricing_model="Unknown",
                is_open_source=None,
                tech_stack=[],
                description="Failed",
                api_available=None,
                language_support=[],
                integration_capabilities=[]
            )
    
    
    def _research_step(self, state: ResearchState) -> Dict[str, Any]:
        # Look in state for extacted_tools attribute, if found give it extracted_tools variable, if not give empty list
        extracted_tools = getattr(state, "extracted_tools", [])
        
        # Edge case handling
        if not extracted_tools:
            print("⚠️ No tools extracted to research. Falling back to direct search.")
            # Search again
            search_results = self.firecrawl.search_companies(state.query, num_results=4)
            # Replace tool_names with title of website searched for
            tool_names = [
                result.get("metadata", {}).get("title", "Unknown")
                for result in search_results.data
            ]
        else:
            # This occurs when extracted_tools is populated
            tool_names = extracted_tools[:4]
    
        print(f"🧐 Researching specific tools: {', '.join(tool_names)}")
        
        # Look up each tool and scrape its website content
        companies = []
        for tool_name in tool_names:
            # Check official site of all tools and find more info
            tool_search_results = self.firecrawl.search_companies(tool_name + " official sit", num_results=1)

            # If tool_search_results is not empty, get the first result, scrape url for data
            if tool_search_results:
                result = tool_search_results.data[0]
                url = result.get("url", "")
                # Create a CompanyInfo object with the tool name and scraped content
                company = CompanyInfo(
                    name=tool_name,
                    description=result.get("markdown", {}),
                    website=url,
                    tech_stack=[],
                    competitors=[]
                )
                
                scraped = self.firecrawl.scrape_company_pages(url)
                # If scraping was successful, analyze the content
                if scraped:
                    content = scraped.markdown
                    analysis = self._analyze_company_content(company.name, content)
                    
                    # Update the company object with analysis results only if scape is successful
                    company.pricing_model = analysis.pricing_model
                    company.is_open_source = analysis.is_open_source
                    company.tech_stack = analysis.tech_stack
                    company.description = analysis.description
                    company.api_available = analysis.api_available
                    company.language_support = analysis.language_support
                    company.integration_capabilities = analysis.integration_capabilities
                    
                companies.append(company)
                
        return {"companies": companies}