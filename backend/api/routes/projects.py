from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..database import get_db
from ..auth import get_current_user
from bson import ObjectId
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

class ProjectCreateRequest(BaseModel):
    name: str
    description: str = ""

@router.post("/", response_model=dict)
async def create_project(project: ProjectCreateRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    new_project = {
        "name": project.name,
        "description": project.description,
        "owner_id": current_user["id"],
        "members": [current_user["id"]]
    }
    result = await db.projects.insert_one(new_project)
    return {"id": str(result.inserted_id), "name": new_project["name"]}

@router.get("/", response_model=List[dict])
async def list_projects(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    # A user can see projects they own or are members of
    cursor = db.projects.find({
        "$or": [
            {"owner_id": current_user["id"]},
            {"members": current_user["id"]}
        ]
    })
    projects = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        projects.append(doc)
    return projects

@router.get("/{project_id}", response_model=dict)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user["id"] != project["owner_id"] and current_user["id"] not in project.get("members", []):
        raise HTTPException(status_code=403, detail="Not authorized to access this project")

    project["id"] = str(project["_id"])
    del project["_id"]
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    project = await db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user["id"] != project["owner_id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only the owner or an admin can delete this project")

    await db.projects.delete_one({"_id": ObjectId(project_id)})
    return {"status": "deleted"}
