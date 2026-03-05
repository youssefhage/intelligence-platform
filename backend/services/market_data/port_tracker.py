"""Lebanese port and customs data tracker for import delay monitoring."""

import json
from datetime import datetime

import httpx
import structlog
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.alert import Alert, AlertSeverity, AlertType

logger = structlog.get_logger()


class PortStatus:
    """Represents current port operational status."""

    def __init__(
        self,
        port_name: str,
        status: str,
        congestion_level: str,
        avg_wait_days: float,
        notes: str = "",
    ):
        self.port_name = port_name
        self.status = status  # operational, limited, closed
        self.congestion_level = congestion_level  # low, medium, high, severe
        self.avg_wait_days = avg_wait_days
        self.notes = notes
        self.checked_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "port_name": self.port_name,
            "status": self.status,
            "congestion_level": self.congestion_level,
            "avg_wait_days": self.avg_wait_days,
            "notes": self.notes,
            "checked_at": self.checked_at.isoformat(),
        }


class PortTracker:
    """Monitors Lebanese port operations and shipping delays.

    Tracks Beirut Port and Tripoli Port status, congestion levels,
    and estimated processing times for import containers.
    """

    # Default port configurations
    TRACKED_PORTS = [
        {
            "name": "Beirut Port",
            "code": "LBBEY",
            "is_primary": True,
            "typical_wait_days": 5,
        },
        {
            "name": "Tripoli Port",
            "code": "LBKYE",
            "is_primary": False,
            "typical_wait_days": 3,
        },
    ]

    # MarineTraffic and similar services for vessel tracking
    VESSEL_TRACKING_SOURCES = [
        "https://www.marinetraffic.com/en/data/?asset_type=ports&columns=flag,shipname,imo",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = httpx.AsyncClient(timeout=30.0)
        self._port_statuses: dict[str, PortStatus] = {}

    async def check_port_status(self) -> list[dict]:
        """Check current status of all tracked Lebanese ports."""
        statuses = []

        for port in self.TRACKED_PORTS:
            status = await self._fetch_port_data(port)
            self._port_statuses[port["name"]] = status
            statuses.append(status.to_dict())

            # Alert if port congestion is high
            if status.congestion_level in ("high", "severe"):
                await self._create_port_alert(port, status)

        logger.info("Port status check complete", ports=len(statuses))
        return statuses

    async def _fetch_port_data(self, port: dict) -> PortStatus:
        """Fetch port operational data.

        Attempts to scrape real port data. Falls back to a heuristic-based
        estimate using the configured typical wait times.
        """
        try:
            # Try UNCTAD port performance data
            url = f"https://unctadstat.unctad.org/api/port/{port['code']}/performance"
            response = await self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                return PortStatus(
                    port_name=port["name"],
                    status="operational",
                    congestion_level=self._classify_congestion(
                        data.get("avg_turnaround_hours", 120)
                    ),
                    avg_wait_days=data.get("avg_turnaround_hours", 120) / 24,
                    notes=f"UNCTAD data as of {datetime.utcnow().date()}",
                )
        except Exception as e:
            logger.debug("UNCTAD port data unavailable", port=port["name"], error=str(e))

        # Fallback: return typical operational data
        return PortStatus(
            port_name=port["name"],
            status="operational",
            congestion_level="medium" if port["is_primary"] else "low",
            avg_wait_days=port["typical_wait_days"],
            notes="Based on typical operational parameters",
        )

    def _classify_congestion(self, turnaround_hours: float) -> str:
        if turnaround_hours > 240:
            return "severe"
        if turnaround_hours > 168:
            return "high"
        if turnaround_hours > 96:
            return "medium"
        return "low"

    async def _create_port_alert(self, port: dict, status: PortStatus):
        """Create an alert for port congestion issues."""
        severity = (
            AlertSeverity.CRITICAL
            if status.congestion_level == "severe"
            else AlertSeverity.WARNING
        )
        alert = Alert(
            alert_type=AlertType.SUPPLY_DISRUPTION,
            severity=severity,
            title=f"Port congestion: {port['name']}",
            message=(
                f"{port['name']} is experiencing {status.congestion_level} congestion "
                f"with average wait time of {status.avg_wait_days:.1f} days. "
                f"{status.notes}"
            ),
            related_entity_type="port",
            action_recommended=(
                f"Consider routing shipments through {'Tripoli Port' if port['is_primary'] else 'Beirut Port'} "
                f"as alternative. Review incoming shipment ETAs and adjust inventory plans."
            ),
        )
        self.db.add(alert)
        await self.db.commit()

    async def get_shipping_routes_status(self) -> dict:
        """Get status of key shipping routes to Lebanon."""
        routes = {
            "suez_canal": {
                "name": "Suez Canal → Mediterranean → Beirut",
                "status": "operational",
                "typical_transit_days": 25,
                "risk_level": "medium",
                "notes": "Primary route for Asian imports (rice, palm oil)",
            },
            "mediterranean_direct": {
                "name": "Mediterranean Direct (Turkey, EU)",
                "status": "operational",
                "typical_transit_days": 5,
                "risk_level": "low",
                "notes": "Short route for Turkish and European suppliers",
            },
            "black_sea": {
                "name": "Black Sea → Mediterranean → Beirut",
                "status": "operational",
                "typical_transit_days": 10,
                "risk_level": "high",
                "notes": "Key route for Ukrainian wheat/sunflower oil. Conflict risk.",
            },
            "south_america": {
                "name": "South America → Mediterranean → Beirut",
                "status": "operational",
                "typical_transit_days": 30,
                "risk_level": "low",
                "notes": "Route for Brazilian sugar, Argentine soy oil",
            },
            "overland_syria": {
                "name": "Overland via Syria",
                "status": "limited",
                "typical_transit_days": 3,
                "risk_level": "critical",
                "notes": "Severely disrupted by conflict. Avoid for critical supplies.",
            },
        }

        # Check for Red Sea / Suez disruptions
        try:
            response = await self.client.get(
                "https://www.lsci.unctad.org/data/country/LB"
            )
            if response.status_code == 200:
                routes["connectivity_index"] = {
                    "source": "UNCTAD LSCI",
                    "note": "Lebanon Liner Shipping Connectivity Index",
                }
        except Exception:
            pass

        return {
            "routes": routes,
            "ports": [s.to_dict() for s in self._port_statuses.values()],
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def get_import_timeline_estimate(
        self, origin_region: str, commodity_name: str
    ) -> dict:
        """Estimate total import timeline from order to warehouse."""
        # Base transit times by origin
        transit_days = {
            "South Asia": 22,
            "Southeast Asia": 25,
            "Black Sea": 10,
            "Eastern Europe": 8,
            "South America": 30,
            "Western Europe": 7,
            "Middle East": 5,
            "Oceania": 35,
            "North America": 25,
        }

        base_transit = transit_days.get(origin_region, 20)

        # Port processing estimate
        port_status = self._port_statuses.get("Beirut Port")
        port_processing = port_status.avg_wait_days if port_status else 5

        # Customs clearance (Lebanon customs can take 3-10 days)
        customs_days = 5

        total = base_transit + port_processing + customs_days

        return {
            "commodity": commodity_name,
            "origin_region": origin_region,
            "ocean_transit_days": base_transit,
            "port_processing_days": round(port_processing, 1),
            "customs_clearance_days": customs_days,
            "total_estimated_days": round(total, 1),
            "recommendation": (
                f"Order {commodity_name} at least {int(total * 1.3)} days before needed "
                f"to account for potential delays."
            ),
        }

    async def close(self):
        await self.client.aclose()
