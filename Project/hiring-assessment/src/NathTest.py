import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================
# OPTION 2: Load from .env file (Recommended)
# ============================================
# Try to load from .env file in parent directory
env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)
    print("📄 Loaded configuration from .env file")
else:
    print("⚠️  No .env file found - using environment variables or hardcoded keys")

# ============================================
# Verify API keys are set
# ============================================
print("\n🔑 API Key Status:")
if os.getenv('HOLISTIC_AI_TEAM_ID') and os.getenv('HOLISTIC_AI_API_TOKEN'):
    print("  ✅ Holistic AI Bedrock credentials loaded (will use Bedrock)")
elif os.getenv('OPENAI_API_KEY'):
    print("  ⚠️  OpenAI API key loaded (Bedrock credentials not set)")
    print("     💡 Tip: Set HOLISTIC_AI_TEAM_ID and HOLISTIC_AI_API_TOKEN to use Bedrock (recommended)")
else:
    print("  ⚠️  No API keys found")
    print("     Set Holistic AI Bedrock credentials (recommended) or OpenAI key")

if os.getenv('VALYU_API_KEY'):
    key_preview = os.getenv('VALYU_API_KEY')[:10] + "..."
    print(f"  ✅ Valyu API key loaded: {key_preview}")
else:
    print("  ⚠️  Valyu API key not found - search tool will not work")

print("\n📁 Working directory:", Path.cwd())


# ============================================
# Import Holistic AI Bedrock helper function
# ============================================
# Import from core module (recommended)
import sys
sys.path.insert(0, './core')
from react_agent.holistic_ai_bedrock import HolisticAIBedrockChat, get_chat_model
print("\n✅ Holistic AI Bedrock helper function loaded")


# Import official packages
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

print("\n✅ All imports successful!")




import time

# Example 1: Direct LLM Call (Simple)
# print("="*70)
# print("EXAMPLE 1: Direct LLM Call")
# print("="*70)

# # Use the helper function - uses Holistic AI Bedrock by default
# llm = get_chat_model("claude-3-5-sonnet")  # Uses Holistic AI Bedrock (recommended)

# question = "What is a skateboard?"
# print(f"\n❓ Question: {question}")

# start_time = time.time()
# response = llm.invoke(question)
# elapsed = time.time() - start_time

# print(f"\n💬 Response: {response.content}")
# print(f"\n⏱️  Time: {elapsed:.2f}s")
# print("\n✅ Simple and fast!")
# print("❌ But... can't use tools, can't reason through steps, single response only")