# backend/routes/agents.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.models import models, models as pydantic_schemas
from backend.models.models import get_db

router = APIRouter(
    prefix="/api/agents",
    tags=["Agents"],
    responses={404: {"description": "Not found"}},
)

@router.get("/status", 
            summary="Get Status of All AI Agents",
            response_model=List[pydantic_schemas.AgentSchema])
def get_agents_status(db: Session = Depends(get_db)):
    """
    Retrieves the status and details of all registered AI agents from the database.
    
    This endpoint is useful for system monitoring to ensure all agents are active and correctly configured.
    """
    try:
        agents = db.query(models.Agent).all()
        if not agents:
            raise HTTPException(status_code=404, detail="No agents found in the database.")
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching agents: {str(e)}")

@router.get("/{agent_name}", 
            summary="Get Details of a Specific Agent",
            response_model=pydantic_schemas.AgentSchema)
def get_agent_details(agent_name: str, db: Session = Depends(get_db)):
    """
    Retrieves detailed information for a single agent by its name.
    """
    try:
        agent = db.query(models.Agent).filter(models.Agent.name == agent_name).first()
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent with name '{agent_name}' not found.")
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
