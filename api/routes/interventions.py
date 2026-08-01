"""PRAXIS Interventions API Route — §9.

Handles resolution of system intervention prompts (nudges, Do Blocks, drift proposals).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.database import get_db
from api import clock
from api.schemas import InterventionResolveRequest, InterventionResolveResponse
from api.models import DbIntervention, DbAspiration, DbSelfSpec, DbTheme
from sqlalchemy import select, desc

router = APIRouter(prefix="/api/interventions", tags=["Interventions"])


@router.post("/{intervention_id}/resolve", response_model=InterventionResolveResponse)
async def resolve_intervention(
    intervention_id: str,
    req: InterventionResolveRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resolve an active intervention. For drift proposals, handles accepting or rejecting changes."""
    # 1. Fetch intervention
    intervention = await db.get(DbIntervention, intervention_id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found.")

    # 2. Update resolved timestamp
    intervention.resolved_at = clock.now()

    # 3. Process specific resolution logic based on intervention type
    result = {"status": "resolved"}
    
    if intervention.type == "drift_proposal" and req.accept:
        # User accepted the identity update!
        # Change aspirations and focus themes in the DB.
        # Find latest self spec
        spec_stmt = select(DbSelfSpec).where(DbSelfSpec.user_id == intervention.user_id).order_by(desc(DbSelfSpec.created_at))
        spec_res = await db.execute(spec_stmt)
        self_spec = spec_res.scalars().first()

        if self_spec:
            # Shift the drifting theme status
            # For example, we create a new aspiration or update the existing retired status.
            # In our demo scenario, we retired the public speaking aspiration and activate systems design
            asp_stmt = select(DbAspiration).where(DbAspiration.self_spec_id == self_spec.id)
            asp_res = await db.execute(asp_stmt)
            aspirations = asp_res.scalars().all()
            
            for asp in aspirations:
                if "speaker" in asp.text.lower():
                    asp.status = "retired"
                    asp.retired_at = clock.now()
                
            # Add a new active aspiration representing the drifted focus
            new_asp = DbAspiration(
                id=f"asp_drift_{clock.now().strftime('%H%M%S')}",
                self_spec_id=self_spec.id,
                text="become a software systems architect",
                status="active",
                created_at=clock.now()
            )
            db.add(new_asp)
            result["drift_applied"] = True
            result["new_aspiration"] = new_asp.text

    await db.commit()
    return InterventionResolveResponse(result=result)
