"""
HR Recruiter AI Agent - Automated Resume Screening and Ranking System

This module provides an AI-powered agent that:
- Reads job descriptions from files or URLs
- Matches resumes against job requirements using an MCP server
- Generates comprehensive ranking reports

Author: AI Assistant
Date: October 13, 2025
"""

import os
import json
import asyncio
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Environment Variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MCP_CONFIG_FILE = "mcp.json"

# Constants
MCP_TOOL_RANK_RESUMES = "rank_resumes_mcp"
MCP_TOOL_FETCH_JOB_DESC = "fetch_job_description_mcp"
SUPPORTED_FILE_EXTENSIONS = ('.txt', '.pdf', '.docx')
MAX_FILE_SIZE_MB = 10

# Configuration
RESUMES_FOLDER = "resumes"
JOB_DESCRIPTIONS_FOLDER = "job_descriptions"
RESULTS_FOLDER = "results"

# Ensure folders exist
os.makedirs(RESUMES_FOLDER, exist_ok=True)
os.makedirs(JOB_DESCRIPTIONS_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Load MCP configuration
try:
    with open('mcp.json', 'r') as f:
        mcp_config = json.load(f)
    server_config = mcp_config['mcpServers']['default-server']
    command = server_config['command']
    args = server_config['args']
    env = server_config.get('env', {})
    logger.info("MCP configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load MCP configuration: {e}")
    raise

# Cache for MCP tools
_mcp_tools_cache: Optional[List[Any]] = None

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove any path components
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric characters except dots, underscores, and hyphens
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename


def validate_file_path(file_path: str, max_size_mb: int = MAX_FILE_SIZE_MB) -> None:
    """
    Validate file path and size.
    
    Args:
        file_path: Path to validate
        max_size_mb: Maximum file size in MB
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is too large or invalid type
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(f"File too large: {file_size_mb:.2f}MB (max: {max_size_mb}MB)")
    
    if not file_path.lower().endswith(SUPPORTED_FILE_EXTENSIONS):
        raise ValueError(f"Unsupported file type. Supported: {SUPPORTED_FILE_EXTENSIONS}")


async def discover_and_invoke_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Discover and invoke an MCP tool.
    
    Args:
        tool_name: Name of the MCP tool to invoke
        **kwargs: Arguments to pass to the tool
        
    Returns:
        Dict containing the tool result
        
    Raises:
        ValueError: If tool not found
        Exception: For connection or execution errors
    """
    global _mcp_tools_cache
    
    try:
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Use cached tools if available
                if _mcp_tools_cache is None:
                    tools_list = await session.list_tools()
                    _mcp_tools_cache = tools_list.tools
                    logger.info(f"✅ Discovered MCP tools: {[t.name for t in _mcp_tools_cache]}")
                
                # Find the tool
                tool_info = next((t for t in _mcp_tools_cache if t.name == tool_name), None)
                if not tool_info:
                    raise ValueError(f"Tool '{tool_name}' not found on MCP server. Available: {[t.name for t in _mcp_tools_cache]}")
                
                # Invoke the tool
                logger.info(f"Invoking MCP tool: {tool_name}")
                result = await session.call_tool(tool_name, kwargs)
                
                # Parse the result content
                if result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            return json.loads(content_item.text)
                
                logger.warning(f"No text content in result from {tool_name}")
                return {}
                
    except Exception as e:
        logger.error(f"Error invoking MCP tool '{tool_name}': {e}")
        raise

def read_file_content(file_path: str) -> str:
    """
    Read content from various file formats.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Text content of the file
        
    Raises:
        ValueError: If file type is unsupported
        FileNotFoundError: If file doesn't exist
    """
    validate_file_path(file_path)
    
    try:
        if file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif file_path.lower().endswith('.pdf'):
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
            except ImportError:
                raise ImportError("PyPDF2 is required for PDF support. Install with: pip install PyPDF2")
                
        elif file_path.lower().endswith('.docx'):
            try:
                import docx
                doc = docx.Document(file_path)
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                return text
            except ImportError:
                raise ImportError("python-docx is required for DOCX support. Install with: pip install python-docx")
                
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
            
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def extract_job_title_from_content(content: str) -> str:
    """
    Extract job title from job description content.
    
    Args:
        content: Job description text
        
    Returns:
        Extracted job title or 'Unknown Position'
    """
    lines = content.split('\n')
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if line.startswith('Job Title:'):
            return line.replace('Job Title:', '').strip()
        elif line and len(line) < 50 and not line.startswith('-'):
            # First non-empty, short line might be the title
            return line
    return "Unknown Position"

@tool
def get_job_description_content(job_description_file: str) -> str:
    """
    Retrieves the content of a job description from a file or URL.

    Args:
        job_description_file: The filename or URL of the job description.

    Returns:
        The text content of the job description.
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If URL fetching fails
    """
    try:
        if job_description_file.startswith(('http://', 'https://')):
            # Use MCP tool for URL
            logger.info(f"Fetching job description from URL: {job_description_file}")
            result = asyncio.run(discover_and_invoke_tool(MCP_TOOL_FETCH_JOB_DESC, url=job_description_file))
            return result.get("content", "")
        else:
            # Sanitize filename to prevent path traversal
            safe_filename = sanitize_filename(job_description_file)
            file_path = os.path.join(JOB_DESCRIPTIONS_FOLDER, safe_filename)
            logger.info(f"Reading job description from file: {file_path}")
            return read_file_content(file_path)
    except Exception as e:
        logger.error(f"Error getting job description: {e}")
        raise

@tool
def match_resumes(job_description_content: str) -> str:
    """
    Matches resumes against the job description using MCP server.

    Args:
        job_description_content: The text content of the job description.

    Returns:
        A JSON string containing the combined analysis results.
        
    Raises:
        ValueError: If no resumes found
        Exception: For MCP server errors
    """
    try:
        # Collect resume files
        resume_files = [
            os.path.join(RESUMES_FOLDER, f) 
            for f in os.listdir(RESUMES_FOLDER) 
            if f.lower().endswith(SUPPORTED_FILE_EXTENSIONS)
        ]
        
        if not resume_files:
            raise ValueError(f"No resume files found in {RESUMES_FOLDER}")
        
        logger.info(f"Found {len(resume_files)} resume(s) to analyze")
        
        # Read resume contents
        resume_texts = []
        resume_filenames = []
        
        for file_path in resume_files:
            try:
                content = read_file_content(file_path)
                resume_texts.append(content)
                resume_filenames.append(os.path.basename(file_path))
            except Exception as e:
                logger.warning(f"Skipping {file_path}: {e}")
                continue
        
        if not resume_texts:
            raise ValueError("Failed to read any resume files")
        
        # Use MCP tool for ranking resumes
        result = asyncio.run(discover_and_invoke_tool(
            MCP_TOOL_RANK_RESUMES, 
            job_description=job_description_content, 
            resume_texts=resume_texts,
            resume_filenames=resume_filenames
        ))
        
        # Transform the result to match expected format
        rankings = result.get("rankings", [])
        transformed_results = []
        
        for rank_data in rankings:
            # Extract name from filename (remove extension and format)
            filename = rank_data.get("resumeFilename", "Unknown")
            name = Path(filename).stem.replace('_', ' ').title()
            
            transformed_results.append({
                "name": name,
                "percentage": rank_data.get("score", 0),
                "skills_available": rank_data.get("strengths", []),
                "skills_missing": rank_data.get("improvements", []),
                "rank": rank_data.get("rank", 0)
            })
        
        logger.info(f"Successfully analyzed {len(transformed_results)} resume(s)")
        return json.dumps(transformed_results)
        
    except Exception as e:
        logger.error(f"Error matching resumes: {e}")
        raise

@tool
def generate_report(analysis_data: str) -> str:
    """
    Generates a human-readable report from the analysis data.

    Args:
        analysis_data: JSON string of analysis results.

    Returns:
        The path to the generated report file.
        
    Raises:
        json.JSONDecodeError: If analysis_data is invalid JSON
        IOError: If report file cannot be written
    """
    try:
        data = json.loads(analysis_data)
        
        # Try to extract job title from first candidate's data or use default
        job_title = "Position"
        if data and len(data) > 0:
            # Try reading the job description file again
            try:
                job_desc_file = os.path.join(JOB_DESCRIPTIONS_FOLDER, "software_engineer.txt")
                if os.path.exists(job_desc_file):
                    with open(job_desc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        job_title = extract_job_title_from_content(content)
            except Exception:
                pass  # Use default if extraction fails
        
        # Sort by percentage (score)
        sorted_data = sorted(data, key=lambda x: x.get('percentage', 0), reverse=True)
        
        # Create safe filename
        safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', job_title)
        report_path = os.path.join(RESULTS_FOLDER, f"analysis_report_{safe_title}.md")
        
        logger.info(f"Generating report for: {job_title}")
        
        # Generate report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Recruitment Analysis Report\n\n")
            f.write(f"**Position:** {job_title}\n\n")
            f.write(f"**Date:** {os.environ.get('REPORT_DATE', 'N/A')}\n\n")
            f.write(f"**Total Candidates Analyzed:** {len(sorted_data)}\n\n")
            f.write("---\n\n")
            
            for rank, candidate in enumerate(sorted_data, start=1):
                f.write(f"## Rank {rank}: {candidate.get('name', 'Unknown')}\n\n")
                f.write(f"**Match Score:** {candidate.get('percentage', 0)}%\n\n")
                
                skills = candidate.get('skills_available', [])
                if skills:
                    f.write(f"**Strengths:**\n")
                    for skill in skills:
                        f.write(f"- {skill}\n")
                    f.write("\n")
                
                improvements = candidate.get('skills_missing', [])
                if improvements:
                    f.write(f"**Areas for Improvement:**\n")
                    for improvement in improvements:
                        f.write(f"- {improvement}\n")
                    f.write("\n")
                
                f.write("---\n\n")
            
            # Summary
            if sorted_data:
                avg_score = sum(c.get('percentage', 0) for c in sorted_data) / len(sorted_data)
                f.write(f"## Summary\n\n")
                f.write(f"- **Average Match Score:** {avg_score:.1f}%\n")
                f.write(f"- **Top Candidate:** {sorted_data[0].get('name', 'Unknown')} ({sorted_data[0].get('percentage', 0)}%)\n")
        
        logger.info(f"Report generated successfully: {report_path}")
        return report_path
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    try:
        # Validate environment
        if not GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY not found in environment")
            print("Error: GOOGLE_API_KEY not set. Please check your .env file.")
            exit(1)
        
        if not MCP_CONFIG_FILE or not os.path.exists(MCP_CONFIG_FILE):
            logger.error(f"MCP config file not found: {MCP_CONFIG_FILE}")
            print(f"Error: MCP config file not found at {MCP_CONFIG_FILE}")
            exit(1)
        
        logger.info("Starting HR Recruiter Agent")
        
        # Instantiate LLM
        llm = ChatGoogleGenerativeAI(
            temperature=0.1, 
            model="gemini-2.0-flash", 
            google_api_key=GOOGLE_API_KEY, 
            convert_system_message_to_human=True
        )
        
        # Define tools
        tools = [get_job_description_content, match_resumes, generate_report]
        
        # System prompt
        system_prompt = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""

        prompt = PromptTemplate.from_template(system_prompt)
        
        # Create agent
        agent = create_react_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        # Sample input (can be modified or taken from command line)
        sample_input = "software_engineer.txt"
        
        print("\n" + "="*60)
        print("HR Recruiter AI Agent - Starting Analysis")
        print("="*60 + "\n")
        
        logger.info(f"Processing input: {sample_input}")
        result = agent_executor.invoke({"input": sample_input})
        
        print("\n" + "="*60)
        print("Analysis Complete!")
        print("="*60 + "\n")
        print(result['output'])
        
        logger.info("Agent execution completed successfully")
        exit(0)
        
    except KeyboardInterrupt:
        logger.info("Agent execution interrupted by user")
        print("\n\nExecution interrupted by user.")
        exit(130)
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        print(f"\n\nError: {e}")
        print("Please check the logs for more details.")
        exit(1)