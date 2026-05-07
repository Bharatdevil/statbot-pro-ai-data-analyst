import os
import logging
import pandas as pd
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("statbotpro.ai.gemini_agent")


def analyze_csv_with_gemini(df: pd.DataFrame, query: str) -> str:
    """
    Use Gemini and LangChain Pandas DataFrame Agent to analyze the dataframe with a natural language query.
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not set in environment.")
            raise ValueError("GOOGLE_API_KEY not set.")
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=api_key, temperature=0)
        agent = create_pandas_dataframe_agent(llm, df, verbose=False, allow_dangerous_code=True)
        logger.info("Sending query to Gemini agent: %s", query)
        answer = agent.invoke(query)
        return answer["output"]
    except Exception as e:
        logger.error("AI analysis error: %s", e)
        raise
