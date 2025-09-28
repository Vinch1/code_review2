from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class AuditReq(BaseModel):
    filter_instruction: Optional[str] = ""
    scan_instruction: Optional[str] = ""
    pr_number: int
    repo_name: str

class FilteringSummary(BaseModel):
    total_original_findings: int
    excluded_findings: int
    kept_findings: int
    filter_analysis: Dict[str, Any]
    excluded_findings_details: List[Dict[str, Any]] 

class AuditResp(BaseModel):
    pr_number: int
    repo: str
    findings: List[Dict[str, Any]] 
    analysis_summary: Dict[str, Any]
    filtering_summary: FilteringSummary