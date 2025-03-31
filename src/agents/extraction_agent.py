from typing import Dict, Any, Union, List
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import StringPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import AgentAction, AgentFinish
from langchain.agents.format_scratchpad import format_log_to_str
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field
import json
import re
import logging
from datetime import datetime, date

from ..validators.models import ContractData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContractExtractionPrompt(StringPromptTemplate, BaseModel):
    """Prompt template for contract extraction."""
    template: str = """You are a contract data extraction agent. Your task is to extract specific information from the provided document content.

Please analyze the document carefully and extract the following fields:

1. Client Name: Look for the company or individual name that is the client in this contract.
2. Client Address: Look for the complete address of the client. This should include street address, city, state, and any other location details.
3. Machine Names: Look for machine names or model numbers mentioned in the document. If you see entries like "Base Machine" and "Monitizer DISCOVER for Base Machine", only include the base machine name.
4. Purchase Order: Look for a purchase order (PO) number or reference number.
5. Effective Date: Look for the contract start date or effective date.
6. Subscription Duration: Look for the subscription period in months.

Return the extracted information in a valid JSON object with these fields:
{{
    "client_name": "string",
    "address": "string",
    "machine_names": ["string"],
    "purchase_order": "string",
    "effective_date": "YYYY-MM-DD",
    "subscription_duration_months": integer
}}

Important Rules:
- Extract real values only, do not return placeholder text like {{client_name}} or {{address}}
- For machine names, only include the base machine names, not any "Monitizer DISCOVER for" entries
- For dates, use the YYYY-MM-DD format
- For subscription duration, return only the number (e.g., 12 for 12 months)
- If a field is not found, use null or an empty list [] for machine_names
- Look for address information near the client name or in the header section
- Pay special attention to tables, as they often contain machine details

Document Content:
{content}"""

    input_variables: List[str] = ["content"]

    def format(self, **kwargs) -> str:
        """Format the prompt with the given variables."""
        try:
            formatted = self.template.format(**kwargs)
            logger.info("Successfully formatted prompt")
            return formatted
        except KeyError as e:
            logger.error(f"Missing required variable in prompt: {e}")
            raise
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            raise

class ContractExtractionAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-3.5-turbo",
            openai_api_key=openai_api_key
        )
        self.prompt = ContractExtractionPrompt()

    def extract(self, text: str) -> Dict[str, Any]:
        """Extract contract information from text using LLM."""
        try:
            logger.info("Starting LLM-based extraction...")
            logger.info("Input text:")
            logger.info("-" * 50)
            logger.info(text)
            logger.info("-" * 50)
            
            # Format the prompt with the document content
            try:
                formatted_prompt = self.prompt.format(content=text)
                logger.info("Formatted prompt:")
                logger.info("-" * 50)
                logger.info(formatted_prompt)
                logger.info("-" * 50)
            except Exception as e:
                logger.error(f"Error formatting prompt: {e}")
                raise
            
            # Get response from LLM
            response = self.llm.invoke(formatted_prompt)
            logger.info("LLM response:")
            logger.info("-" * 50)
            logger.info(response.content)
            logger.info("-" * 50)
            
            # Parse the response
            try:
                # Extract JSON from the response
                json_str = response.content
                
                # Clean up the response
                # Remove any markdown code blocks
                json_str = re.sub(r'```json\s*|\s*```', '', json_str)
                # Remove any leading/trailing whitespace
                json_str = json_str.strip()
                # Remove any leading/trailing newlines
                json_str = re.sub(r'^\s+|\s+$', '', json_str)
                
                logger.info("Cleaned JSON string:")
                logger.info("-" * 50)
                logger.info(json_str)
                logger.info("-" * 50)
                
                # Parse the JSON
                extracted_data = json.loads(json_str)
                
                logger.info("LLM extracted data:")
                logger.info("-" * 50)
                logger.info(extracted_data)
                logger.info("-" * 50)
                
                # Validate the data
                try:
                    validated_data = ContractData(**extracted_data)
                    logger.info("Final validated data:")
                    logger.info("-" * 50)
                    logger.info(validated_data.dict())
                    logger.info("-" * 50)
                    return validated_data.dict()
                except Exception as e:
                    logger.error(f"Validation error: {e}")
                    # Return default data if validation fails
                    return {
                        "client_name": "",
                        "effective_date": date.today(),
                        "machine_names": [],
                        "subscription_duration_months": 12,
                        "purchase_order": ""
                    }
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error("Failed JSON string:")
                logger.error("-" * 50)
                logger.error(json_str)
                logger.error("-" * 50)
                # Return default data if JSON parsing fails
                return {
                    "client_name": "",
                    "effective_date": date.today(),
                    "machine_names": [],
                    "subscription_duration_months": 12,
                    "purchase_order": ""
                }
            
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            # Return default data if extraction fails
            return {
                "client_name": "",
                "effective_date": date.today(),
                "machine_names": [],
                "subscription_duration_months": 12,
                "purchase_order": ""
            } 