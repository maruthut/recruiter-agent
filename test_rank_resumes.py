"""
DEPRECATED: This test file is for stdio mode MCP connection which has been removed.
Please use the main hr_agent.py with Streamable HTTP MCP for resume ranking.

This file is kept for reference only.
"""
import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_rank_resumes():
    """Test the rank_resumes_mcp tool with actual data."""
    
    # Load MCP configuration
    with open('mcp.json', 'r') as f:
        mcp_config = json.load(f)
    
    server_config = mcp_config['mcpServers']['default-server']
    command = server_config['command']
    args = server_config['args']
    env = server_config.get('env', {})
    
    # Read job description
    job_desc_path = "job_descriptions/software_engineer.txt"
    with open(job_desc_path, 'r', encoding='utf-8') as f:
        job_description = f.read()
    
    # Read resumes
    resumes_folder = "resumes"
    resume_files = [os.path.join(resumes_folder, f) for f in os.listdir(resumes_folder) if f.endswith('.txt')]
    resume_texts = []
    resume_filenames = []
    
    for file_path in resume_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            resume_texts.append(f.read())
        resume_filenames.append(os.path.basename(file_path))
    
    print("=" * 80)
    print("Testing rank_resumes_mcp tool")
    print("=" * 80)
    print(f"Job Description Length: {len(job_description)} chars")
    print(f"Number of Resumes: {len(resume_texts)}")
    print(f"Resume Filenames: {resume_filenames}")
    print("=" * 80)
    
    try:
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call the rank_resumes_mcp tool
                result = await session.call_tool(
                    "rank_resumes_mcp",
                    {
                        "job_description": job_description,
                        "resume_texts": resume_texts,
                        "resume_filenames": resume_filenames
                    }
                )
                
                print("\n📋 Raw Result Object:")
                print(f"Type: {type(result)}")
                print(f"Result: {result}")
                print("=" * 80)
                
                print("\n📋 Result Content:")
                if result.content:
                    for i, content_item in enumerate(result.content):
                        print(f"\nContent Item {i}:")
                        print(f"  Type: {type(content_item)}")
                        print(f"  Has text: {hasattr(content_item, 'text')}")
                        if hasattr(content_item, 'text'):
                            print(f"  Text: {content_item.text}")
                            # Try to parse as JSON
                            try:
                                parsed = json.loads(content_item.text)
                                print(f"  Parsed JSON: {json.dumps(parsed, indent=2)}")
                            except:
                                print(f"  (Not valid JSON)")
                
                print("=" * 80)
                print("✅ Test completed!")
                
    except Exception as e:
        print(f"❌ Error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rank_resumes())
