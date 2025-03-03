from typing import Dict, Optional
from app.models.workflows import WorkflowState, WorkflowStatus
import logging

logger = logging.getLogger(__name__)

class WorkflowStateManager:
    def __init__(self):
        self._states: Dict[str, WorkflowState] = {}

    def create_workflow(self, workflow_id: str) -> WorkflowState:
        """Create a new workflow state"""
        state = WorkflowState(workflow_id=workflow_id)
        self._states[workflow_id] = state
        logger.debug(f"Created new workflow state: {state}")
        return state

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state"""
        state = self._states.get(workflow_id)
        logger.debug(f"Retrieved state for workflow {workflow_id}: {state}")
        if state:
            logger.debug(f"Current progress for workflow {workflow_id}: {state.progress}, type: {type(state.progress)}")
        return state

    def update_progress(self, workflow_id: str, progress: float):
        """Update workflow progress (0.0 to 1.0)"""
        if workflow_id in self._states:
            old_progress = self._states[workflow_id].progress
            self._states[workflow_id].progress = float(progress)
            logger.info(f"Updated progress for workflow {workflow_id}: {old_progress} -> {progress}")
            logger.debug(f"State after update: {self._states[workflow_id]}")
            logger.debug(f"Current states: {self._states}")
        else:
            logger.warning(f"Attempted to update progress for non-existent workflow {workflow_id}")
            logger.debug(f"Available workflow states: {list(self._states.keys())}")

    def update_status(self, workflow_id: str, status: WorkflowStatus):
        """Update workflow status"""
        if workflow_id in self._states:
            old_status = self._states[workflow_id].status
            self._states[workflow_id].status = status
            logger.info(f"Updated status for workflow {workflow_id}: {old_status} -> {status}")

    def set_error(self, workflow_id: str, error: str):
        if workflow_id in self._states:
            state = self._states[workflow_id]
            state.status = WorkflowStatus.FAILED
            state.error = error

    def set_result(self, workflow_id: str, result: Dict):
        if workflow_id in self._states:
            state = self._states[workflow_id]
            state.result = result
            state.status = WorkflowStatus.COMPLETED 