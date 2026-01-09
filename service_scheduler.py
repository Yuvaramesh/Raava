"""
Service Scheduler - Manufacturer Service Schedules and Recommendations
Calculates service intervals and provides recommendations based on vehicle data
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ServiceScheduler:
    """Manages manufacturer service schedules and recommendations"""

    def __init__(self):
        # Service intervals by manufacturer (in miles)
        self.service_intervals = {
            "Ferrari": {
                "annual": 10000,
                "minor": 10000,
                "major": 20000,
                "oil_change": 10000,
            },
            "Lamborghini": {
                "annual": 9000,
                "minor": 9000,
                "major": 18000,
                "oil_change": 9000,
            },
            "Porsche": {
                "annual": 10000,
                "minor": 10000,
                "major": 20000,
                "oil_change": 10000,
            },
            "McLaren": {
                "annual": 10000,
                "minor": 10000,
                "major": 20000,
                "oil_change": 10000,
            },
            "Aston Martin": {
                "annual": 10000,
                "minor": 10000,
                "major": 20000,
                "oil_change": 10000,
            },
            "Bentley": {
                "annual": 10000,
                "minor": 10000,
                "major": 20000,
                "oil_change": 10000,
            },
            "Rolls-Royce": {
                "annual": 10000,
                "minor": 10000,
                "major": 20000,
                "oil_change": 10000,
            },
            "Mercedes-AMG": {
                "annual": 10000,
                "minor": 10000,
                "major": 20000,
                "oil_change": 10000,
            },
            "BMW M": {
                "annual": 10000,
                "minor": 10000,
                "major": 20000,
                "oil_change": 10000,
            },
            "Audi RS": {
                "annual": 10000,
                "minor": 10000,
                "major": 20000,
                "oil_change": 10000,
            },
        }

        # Service types with cost estimates (Tier 1 dealer prices)
        self.service_types = {
            "minor_service": {
                "name": "Minor Service",
                "description": "Oil & filter change, basic checks",
                "cost_min": 300,
                "cost_max": 600,
                "duration_hours": 1.5,
                "includes": [
                    "Engine oil change",
                    "Oil filter replacement",
                    "Visual inspection",
                    "Brake check",
                    "Tire pressure check",
                    "Fluid level top-ups",
                ],
            },
            "major_service": {
                "name": "Major Service",
                "description": "Full inspection with major components",
                "cost_min": 600,
                "cost_max": 1500,
                "duration_hours": 3.0,
                "includes": [
                    "All minor service items",
                    "Air filter replacement",
                    "Cabin filter replacement",
                    "Spark plug replacement (if due)",
                    "Brake fluid change",
                    "Coolant system check",
                    "Full vehicle inspection",
                ],
            },
            "annual_service": {
                "name": "Annual Service",
                "description": "Yearly maintenance service",
                "cost_min": 500,
                "cost_max": 800,
                "duration_hours": 2.0,
                "includes": [
                    "Oil & filter change",
                    "Safety inspection",
                    "Brake system check",
                    "Suspension check",
                    "Battery test",
                    "Lights & indicators check",
                ],
            },
            "oil_change": {
                "name": "Oil & Filter Change",
                "description": "Engine oil and filter replacement",
                "cost_min": 200,
                "cost_max": 400,
                "duration_hours": 1.0,
                "includes": [
                    "Premium synthetic oil",
                    "OEM oil filter",
                    "Oil level check",
                    "Sump plug replacement",
                ],
            },
            "brake_service": {
                "name": "Brake Service",
                "description": "Brake pad/disc inspection and replacement",
                "cost_min": 400,
                "cost_max": 2500,
                "duration_hours": 2.5,
                "includes": [
                    "Brake pad replacement",
                    "Brake disc inspection",
                    "Brake fluid check",
                    "Caliper inspection",
                ],
            },
            "tire_service": {
                "name": "Tire Service",
                "description": "Tire rotation, balance, and replacement",
                "cost_min": 300,
                "cost_max": 2000,
                "duration_hours": 1.5,
                "includes": [
                    "Tire rotation",
                    "Wheel balancing",
                    "Tire pressure check",
                    "Tread depth check",
                ],
            },
            "mot": {
                "name": "MOT Test",
                "description": "UK Ministry of Transport annual test",
                "cost_min": 40,
                "cost_max": 60,
                "duration_hours": 1.0,
                "includes": [
                    "Statutory MOT test",
                    "Emissions test",
                    "Safety checks",
                    "Certificate issued",
                ],
            },
        }

    def get_service_recommendations(
        self,
        make: str,
        model: str,
        year: int,
        mileage: int,
        last_service_mileage: Optional[int] = None,
        service_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get service recommendations based on vehicle data

        Args:
            make: Vehicle manufacturer
            model: Vehicle model
            year: Manufacturing year
            mileage: Current mileage
            last_service_mileage: Mileage at last service
            service_type: Specific service type requested

        Returns:
            Dictionary with service recommendations
        """
        intervals = self.service_intervals.get(
            make, self.service_intervals.get("Porsche")
        )

        services_due = []
        urgent_items = []

        # Calculate services due
        if service_type == "scheduled_service" or service_type is None:
            # Check annual service
            if mileage >= intervals["annual"]:
                next_service_mileage = (mileage // intervals["annual"] + 1) * intervals[
                    "annual"
                ]
                miles_until_service = next_service_mileage - mileage

                if miles_until_service <= 1000:
                    service_info = self.service_types["annual_service"].copy()
                    service_info["miles_overdue"] = (
                        abs(miles_until_service) if miles_until_service < 0 else 0
                    )
                    service_info["miles_until_due"] = (
                        miles_until_service if miles_until_service > 0 else 0
                    )
                    services_due.append(service_info)

            # Check minor service
            miles_since_minor = mileage % intervals["minor"]
            if miles_since_minor >= intervals["minor"] - 1000:
                service_info = self.service_types["minor_service"].copy()
                service_info["miles_until_due"] = intervals["minor"] - miles_since_minor
                services_due.append(service_info)

            # Check major service
            miles_since_major = mileage % intervals["major"]
            if miles_since_major >= intervals["major"] - 1000:
                service_info = self.service_types["major_service"].copy()
                service_info["miles_until_due"] = intervals["major"] - miles_since_major
                services_due.append(service_info)

        # Handle specific service types
        elif service_type in ["repair", "upgrade", "inspection"]:
            # For repairs and upgrades, provide general guidance
            if service_type == "repair":
                urgent_items.append("Professional diagnosis recommended")
            elif service_type == "upgrade":
                services_due.append(
                    {
                        "name": "Performance Upgrade Consultation",
                        "description": "Expert guidance on available upgrades",
                        "cost_min": 0,
                        "cost_max": 0,
                        "duration_hours": 1.0,
                    }
                )

        # Calculate total cost estimate
        total_cost_min = sum(s["cost_min"] for s in services_due)
        total_cost_max = sum(s["cost_max"] for s in services_due)

        return {
            "vehicle": {
                "make": make,
                "model": model,
                "year": year,
                "mileage": mileage,
            },
            "service_intervals": intervals,
            "services_due": services_due,
            "urgent_items": urgent_items,
            "total_cost_estimate": {
                "min": total_cost_min,
                "max": total_cost_max,
            },
            "next_service_due": self._calculate_next_service(mileage, intervals),
            "recommendations": self._generate_recommendations(
                mileage, intervals, services_due
            ),
        }

    def _calculate_next_service(self, mileage: int, intervals: Dict) -> Dict[str, Any]:
        """Calculate next service due"""
        annual_interval = intervals["annual"]
        next_service_mileage = ((mileage // annual_interval) + 1) * annual_interval
        miles_until = next_service_mileage - mileage

        return {
            "type": "Annual Service",
            "due_at_mileage": next_service_mileage,
            "miles_until_due": miles_until,
            "overdue": miles_until < 0,
        }

    def _generate_recommendations(
        self, mileage: int, intervals: Dict, services_due: List[Dict]
    ) -> List[str]:
        """Generate service recommendations"""
        recommendations = []

        if not services_due:
            recommendations.append("Vehicle is up to date with services")
            recommendations.append(
                f"Next service due in {self._calculate_next_service(mileage, intervals)['miles_until_due']} miles"
            )
        else:
            recommendations.append("Service due soon - book appointment")
            if len(services_due) > 1:
                recommendations.append(
                    "Multiple services can be combined for efficiency"
                )

        # Age-based recommendations
        current_year = datetime.now().year

        # Add general recommendations
        recommendations.append(
            "Use manufacturer-approved parts for warranty compliance"
        )
        recommendations.append("Keep service records up to date for resale value")

        return recommendations

    def get_service_cost_estimate(
        self, service_type: str, make: str, tier: int = 1
    ) -> Dict[str, Any]:
        """
        Get cost estimate for specific service type

        Args:
            service_type: Type of service
            make: Vehicle manufacturer
            tier: Provider tier (1 = dealer, 2 = specialist)

        Returns:
            Cost estimate with tier adjustment
        """
        service_info = self.service_types.get(
            service_type, self.service_types["minor_service"]
        )

        # Tier 2 (specialists) are typically 30-40% cheaper
        tier_multiplier = 1.0 if tier == 1 else 0.65

        return {
            "service_type": service_type,
            "name": service_info["name"],
            "cost_min": int(service_info["cost_min"] * tier_multiplier),
            "cost_max": int(service_info["cost_max"] * tier_multiplier),
            "duration_hours": service_info["duration_hours"],
            "tier": tier,
        }


# Singleton instance
service_scheduler = ServiceScheduler()
