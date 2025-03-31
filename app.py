import streamlit as st
from pathlib import Path
import os
import logging
from dotenv import load_dotenv
from src.loaders.document_loader import DocumentLoader
from src.agents.extraction_agent import ContractExtractionAgent
from src.generators.contract_generator import ContractGenerator
from src.validators.models import ContractData
from datetime import date, datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
document_loader = DocumentLoader()
extraction_agent = ContractExtractionAgent(os.getenv("OPENAI_API_KEY"))

# Create necessary directories
Path("templates").mkdir(exist_ok=True)
Path("output").mkdir(exist_ok=True)

def process_documents(uploaded_files):
    """Process uploaded documents and extract text content."""
    document_loader = DocumentLoader()
    combined_text = ""
    
    logger.info(f"Processing {len(uploaded_files)} files...")
    
    for uploaded_file in uploaded_files:
        logger.info(f"Processing file: {uploaded_file.name}")
        
        # Save file temporarily
        temp_path = Path(f"temp_{uploaded_file.name}")
        try:
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            logger.info(f"Saved temporary file: {temp_path}")
            
            # Extract text using load_document
            text_content = document_loader.load_document(temp_path)
            logger.info(f"Extracted text from {uploaded_file.name}:")
            logger.info("-" * 50)
            logger.info(text_content)
            logger.info("-" * 50)
            
            if text_content:
                combined_text += text_content + "\n\n"
            else:
                logger.warning(f"No text content extracted from {uploaded_file.name}")
                
        except Exception as e:
            logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
        finally:
            # Clean up temporary file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                    logger.info(f"Cleaned up temporary file: {temp_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up file {temp_path}: {str(e)}")
    
    logger.info("Final combined text:")
    logger.info("=" * 50)
    logger.info(combined_text)
    logger.info("=" * 50)
    
    return combined_text.strip()

def main():
    st.title("Smart Contract Populator")
    
    # Initialize session state
    if 'generated_contract' not in st.session_state:
        st.session_state.generated_contract = None
    if 'template_path' not in st.session_state:
        st.session_state.template_path = None
    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = None
    
    # Create necessary directories
    os.makedirs("templates", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # File upload section
    st.header("Upload Files")
    uploaded_files = st.file_uploader("Upload Documents", type=["pdf", "docx", "txt", "jpg", "jpeg", "png"], accept_multiple_files=True)
    template_file = st.file_uploader("Upload Contract Template", type=["docx"])
    
    if uploaded_files and template_file:
        if st.button("Generate Contract"):
            try:
                # Save template file if not already saved
                if not st.session_state.template_path:
                    template_path = os.path.join("templates", template_file.name)
                    with open(template_path, "wb") as f:
                        f.write(template_file.getvalue())
                    st.session_state.template_path = template_path
                    logger.info(f"Saved template file to: {template_path}")
                
                # Process uploaded documents
                combined_text = process_documents(uploaded_files)
                
                # Extract information using the agent
                extracted_data = extraction_agent.extract(combined_text)
                st.session_state.extracted_data = extracted_data
                
                st.success("Contract information extracted successfully!")
                
            except Exception as e:
                st.error(f"Error processing documents: {str(e)}")
                logger.error(f"Error processing documents: {str(e)}")
    
    # Display and edit extracted information
    if st.session_state.extracted_data:
        st.header("Edit Extracted Information")
        
        # Create editable fields for each piece of information
        edited_data = {}
        edited_data["client_name"] = st.text_input("Client Name", value=st.session_state.extracted_data.get("client_name", ""))
        edited_data["effective_date"] = st.date_input("Effective Date", value=st.session_state.extracted_data.get("effective_date", date.today()))
        edited_data["machine_names"] = st.text_area("Machine Names (one per line)", value="\n".join(st.session_state.extracted_data.get("machine_names", []))).split("\n")
        edited_data["subscription_duration_months"] = st.number_input("Subscription Duration (months)", min_value=1, value=st.session_state.extracted_data.get("subscription_duration_months", 12))
        edited_data["purchase_order"] = st.text_input("Purchase Order", value=st.session_state.extracted_data.get("purchase_order", ""))
        
        if st.button("Generate Final Contract"):
            try:
                # Verify template file exists
                if not os.path.exists(st.session_state.template_path):
                    raise FileNotFoundError(f"Template file not found at: {st.session_state.template_path}")
                
                # Create output directory with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join("output", f"generated_contract_{timestamp}")
                os.makedirs(output_dir, exist_ok=True)
                
                # Create safe filename from PO number
                safe_po = edited_data["purchase_order"].replace("/", "_").replace("\\", "_")
                output_filename = f"generated_contract_{safe_po}.docx"
                output_path = os.path.join(output_dir, output_filename)
                
                # Convert edited data to ContractData model
                contract_data = ContractData(**edited_data)
                
                # Generate the contract
                contract_generator = ContractGenerator(template_path=st.session_state.template_path)
                contract_generator.generate_contract(contract_data, output_path)
                
                # Read the generated contract into memory
                with open(output_path, "rb") as f:
                    st.session_state.generated_contract = f.read()
                    st.session_state.output_filename = output_filename
                
                # Clean up the temporary output file
                try:
                    os.remove(output_path)
                except Exception as e:
                    logger.error(f"Error removing temporary file: {e}")
                
                st.success("Contract generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating contract: {str(e)}")
                logger.error(f"Error generating contract: {str(e)}")
                # Clean up any failed output files
                if 'output_path' in locals():
                    try:
                        os.remove(output_path)
                    except Exception as e:
                        logger.error(f"Error removing failed output file: {e}")
    
    # Download section
    if st.session_state.generated_contract:
        st.header("Download Contract")
        st.markdown("""
        Click the button below to download the generated contract. 
        The file will be saved to your default downloads folder.
        """)
        st.download_button(
            label="Download Contract",
            data=st.session_state.generated_contract,
            file_name=st.session_state.output_filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

if __name__ == "__main__":
    main() 