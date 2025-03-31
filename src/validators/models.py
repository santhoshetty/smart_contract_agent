from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

class ContractData(BaseModel):
    """Contract data model."""
    client_name: str = Field(default="")
    effective_date: date = Field(...)  # Required field, must be a valid date
    machine_names: List[str] = Field(default_factory=list)
    subscription_duration_months: int = Field(default=12)  # Default to 12 months for free subscription
    purchase_order: str = Field(default="")
    address: str = "Unit IV, Darjeeling Road, Kolkata, West Bengal"  # Added with default from the document
    
    class Config:
        json_schema_extra = {
            "example": {
                "client_name": "Acme Corp",
                "effective_date": "2024-03-30",
                "machine_names": ["Machine A", "Machine B"],
                "subscription_duration_months": 12,
                "purchase_order": "PO-12345"
            }
        } 