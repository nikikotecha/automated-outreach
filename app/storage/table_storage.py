from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from azure.data.tables import TableServiceClient, UpdateMode

from app.config import settings


class TableStore:
    def __init__(self) -> None:
        if settings.azure_storage_connection_string:
            self.service = TableServiceClient.from_connection_string(
                settings.azure_storage_connection_string
            )
        else:
            self.service = None
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        if not self.service:
            return
        for table_name in [
            settings.storage_campaigns_table,
            settings.storage_leads_table,
            settings.storage_outreach_table,
        ]:
            self.service.create_table_if_not_exists(table_name)

    def _table(self, name: str):
        if not self.service:
            raise RuntimeError("Storage not configured")
        return self.service.get_table_client(name)

    def create_campaign(self, icp_prompt: str, max_leads: int) -> dict[str, Any]:
        campaign_id = str(uuid.uuid4())
        entity = {
            "PartitionKey": "campaign",
            "RowKey": campaign_id,
            "icp_prompt": icp_prompt,
            "max_leads": max_leads,
            "status": "NEW",
            "created_at": datetime.utcnow().isoformat(),
            "query_count": 0,
        }
        self._table(settings.storage_campaigns_table).upsert_entity(entity)
        return {**entity, "id": campaign_id}

    def update_campaign(self, campaign_id: str, **fields: Any) -> None:
        entity = {"PartitionKey": "campaign", "RowKey": campaign_id, **fields}
        self._table(settings.storage_campaigns_table).update_entity(entity, mode=UpdateMode.MERGE)

    def get_campaign(self, campaign_id: str) -> dict[str, Any] | None:
        try:
            entity = self._table(settings.storage_campaigns_table).get_entity(
                partition_key="campaign", row_key=campaign_id
            )
            return {**entity, "id": campaign_id}
        except Exception:
            return None

    def list_campaigns(self) -> list[dict[str, Any]]:
        table = self._table(settings.storage_campaigns_table)
        return [dict(row) for row in table.query_entities("PartitionKey eq 'campaign'")]

    def upsert_lead(self, campaign_id: str, lead_id: str, payload: dict[str, Any]) -> None:
        entity = {"PartitionKey": campaign_id, "RowKey": lead_id, **payload}
        self._table(settings.storage_leads_table).upsert_entity(entity)

    def list_leads(self, campaign_id: str) -> list[dict[str, Any]]:
        table = self._table(settings.storage_leads_table)
        return [dict(row) for row in table.query_entities(f"PartitionKey eq '{campaign_id}'")]

    def get_lead(self, campaign_id: str, lead_id: str) -> dict[str, Any] | None:
        try:
            return dict(
                self._table(settings.storage_leads_table).get_entity(
                    partition_key=campaign_id, row_key=lead_id
                )
            )
        except Exception:
            return None

    def add_outreach_log(self, campaign_id: str, lead_id: str, event_type: str, payload: dict[str, Any]) -> str:
        log_id = str(uuid.uuid4())
        entity = {
            "PartitionKey": campaign_id,
            "RowKey": log_id,
            "lead_id": lead_id,
            "event_type": event_type,
            "payload": payload,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._table(settings.storage_outreach_table).upsert_entity(entity)
        return log_id
