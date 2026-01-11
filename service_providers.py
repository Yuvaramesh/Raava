"""
Service Provider Aggregator - Tier 1 & 2 Service Providers
Finds official dealerships and specialist independents for luxury vehicles
"""

from typing import Dict, Any, List, Optional
import math


class ServiceProviderAggregator:
    """Aggregates service providers (official dealers and specialists)"""

    def __init__(self):
        # Tier 1: Official Dealerships (Factory authorized)
        self.tier1_providers = {
            "Ferrari": [
                {
                    "name": "Maranello Sales",
                    "locations": ["Egham, Surrey"],
                    "coordinates": (51.4318, -0.5462),
                    "tier": 1,
                    "rating": 4.7,
                    "review_count": 234,
                    "specialties": [
                        "All Ferrari models",
                        "Factory certified",
                        "Warranty service",
                    ],
                    "certifications": ["Ferrari Factory Authorized"],
                    "phone": "01784 434411",
                    "cost_multiplier": 1.5,
                },
                {
                    "name": "HR Owen Ferrari",
                    "locations": ["London"],
                    "coordinates": (51.5074, -0.1278),
                    "tier": 1,
                    "rating": 4.8,
                    "review_count": 456,
                    "specialties": [
                        "Sales & Service",
                        "Heritage models",
                        "Personalization",
                    ],
                    "certifications": ["Ferrari Factory Authorized"],
                    "phone": "020 7751 5826",
                    "cost_multiplier": 1.6,
                },
            ],
            "Lamborghini": [
                {
                    "name": "Lamborghini London",
                    "locations": ["London"],
                    "coordinates": (51.5074, -0.1278),
                    "tier": 1,
                    "rating": 4.8,
                    "review_count": 389,
                    "specialties": [
                        "All Lamborghini models",
                        "Factory warranty",
                        "Ad Personam",
                    ],
                    "certifications": ["Lamborghini Factory Authorized"],
                    "phone": "020 7751 5800",
                    "cost_multiplier": 1.55,
                },
                {
                    "name": "Lamborghini Birmingham",
                    "locations": ["Birmingham"],
                    "coordinates": (52.4862, -1.8904),
                    "tier": 1,
                    "rating": 4.7,
                    "review_count": 267,
                    "specialties": ["Sales", "Service", "Parts"],
                    "certifications": ["Lamborghini Factory Authorized"],
                    "phone": "0121 667 6555",
                    "cost_multiplier": 1.5,
                },
            ],
            "Porsche": [
                {
                    "name": "Porsche Centre London",
                    "locations": ["London"],
                    "coordinates": (51.5074, -0.1278),
                    "tier": 1,
                    "rating": 4.6,
                    "review_count": 678,
                    "specialties": [
                        "All Porsche models",
                        "Classic restoration",
                        "Motorsport",
                    ],
                    "certifications": ["Porsche Factory Authorized"],
                    "phone": "020 7386 0911",
                    "cost_multiplier": 1.4,
                },
                {
                    "name": "Porsche Centre Manchester",
                    "locations": ["Manchester"],
                    "coordinates": (53.4808, -2.2426),
                    "tier": 1,
                    "rating": 4.7,
                    "review_count": 543,
                    "specialties": ["Sales & Service", "Performance upgrades"],
                    "certifications": ["Porsche Factory Authorized"],
                    "phone": "0161 667 5911",
                    "cost_multiplier": 1.35,
                },
            ],
            "McLaren": [
                {
                    "name": "McLaren London",
                    "locations": ["London"],
                    "coordinates": (51.5074, -0.1278),
                    "tier": 1,
                    "rating": 4.9,
                    "review_count": 234,
                    "specialties": ["All McLaren models", "MSO", "Track support"],
                    "certifications": ["McLaren Factory Authorized"],
                    "phone": "020 7544 5700",
                    "cost_multiplier": 1.7,
                },
            ],
            "Aston Martin": [
                {
                    "name": "Aston Martin Works",
                    "locations": ["Newport Pagnell"],
                    "coordinates": (52.0867, -0.7233),
                    "tier": 1,
                    "rating": 4.9,
                    "review_count": 345,
                    "specialties": ["Heritage", "Restoration", "All models"],
                    "certifications": ["Aston Martin Factory Authorized"],
                    "phone": "01908 610620",
                    "cost_multiplier": 1.6,
                },
            ],
        }

        # Tier 2: Specialist Independents (High quality, cost effective)
        self.tier2_providers = {
            "Ferrari": [
                {
                    "name": "Barkaways Ferrari Specialists",
                    "locations": ["Battersea, London"],
                    "coordinates": (51.4775, -0.1647),
                    "tier": 2,
                    "rating": 4.9,
                    "review_count": 543,
                    "specialties": [
                        "Ferrari specialist",
                        "Classic & modern",
                        "40+ years experience",
                    ],
                    "certifications": ["Independent Ferrari Specialist"],
                    "phone": "020 7228 0007",
                    "cost_multiplier": 0.7,
                },
                {
                    "name": "Meridien Modena",
                    "locations": ["Lyndhurst, Hampshire"],
                    "coordinates": (50.8718, -1.5654),
                    "tier": 2,
                    "rating": 4.8,
                    "review_count": 432,
                    "specialties": [
                        "Ferrari & Maserati",
                        "Service & restoration",
                        "Race prep",
                    ],
                    "certifications": ["30+ years Ferrari experience"],
                    "phone": "023 8028 4869",
                    "cost_multiplier": 0.65,
                },
                {
                    "name": "Emblem Sports Cars",
                    "locations": ["Hinckley, Leicestershire"],
                    "coordinates": (52.5406, -1.3739),
                    "tier": 2,
                    "rating": 4.7,
                    "review_count": 389,
                    "specialties": [
                        "Ferrari specialist",
                        "MOT preparation",
                        "Performance upgrades",
                    ],
                    "certifications": ["Independent Ferrari Specialist"],
                    "phone": "01455 234567",
                    "cost_multiplier": 0.68,
                },
            ],
            "Lamborghini": [
                {
                    "name": "Autoshield",
                    "locations": ["Cuffley, Hertfordshire"],
                    "coordinates": (51.7104, -0.1064),
                    "tier": 2,
                    "rating": 4.9,
                    "review_count": 478,
                    "specialties": [
                        "Lamborghini specialist",
                        "Full service & repair",
                        "Performance",
                    ],
                    "certifications": ["Ex-Lamborghini technicians"],
                    "phone": "01707 888890",
                    "cost_multiplier": 0.65,
                },
                {
                    "name": "Performance Marques",
                    "locations": ["Surrey"],
                    "coordinates": (51.3148, -0.5600),
                    "tier": 2,
                    "rating": 4.8,
                    "review_count": 356,
                    "specialties": [
                        "Italian supercar specialist",
                        "Service & MOT",
                        "Upgrades",
                    ],
                    "certifications": ["Independent Lamborghini Specialist"],
                    "phone": "01483 234567",
                    "cost_multiplier": 0.68,
                },
            ],
            "Porsche": [
                {
                    "name": "RPM Technik",
                    "locations": ["Brackley, Northamptonshire"],
                    "coordinates": (52.0334, -1.1463),
                    "tier": 2,
                    "rating": 4.9,
                    "review_count": 789,
                    "specialties": [
                        "Porsche specialist",
                        "Service & tuning",
                        "Classic restoration",
                    ],
                    "certifications": ["Independent Porsche Specialist"],
                    "phone": "01280 702389",
                    "cost_multiplier": 0.6,
                },
                {
                    "name": "Ninemeister",
                    "locations": ["Swindon, Wiltshire"],
                    "coordinates": (51.5558, -1.7797),
                    "tier": 2,
                    "rating": 4.9,
                    "review_count": 654,
                    "specialties": ["Air-cooled & modern", "Performance", "Race prep"],
                    "certifications": ["Independent Porsche Specialist"],
                    "phone": "01793 615000",
                    "cost_multiplier": 0.62,
                },
                {
                    "name": "Design 911",
                    "locations": ["Preston, Lancashire"],
                    "coordinates": (53.7632, -2.7031),
                    "tier": 2,
                    "rating": 4.8,
                    "review_count": 567,
                    "specialties": [
                        "Classic 911 specialist",
                        "Parts & service",
                        "Restoration",
                    ],
                    "certifications": ["Independent Porsche Specialist"],
                    "phone": "01772 566600",
                    "cost_multiplier": 0.63,
                },
            ],
            "McLaren": [
                {
                    "name": "McLaren Specialists UK",
                    "locations": ["Birmingham"],
                    "coordinates": (52.4862, -1.8904),
                    "tier": 2,
                    "rating": 4.8,
                    "review_count": 234,
                    "specialties": [
                        "McLaren service",
                        "Performance upgrades",
                        "Track prep",
                    ],
                    "certifications": ["Ex-McLaren technicians"],
                    "phone": "0121 123 4567",
                    "cost_multiplier": 0.7,
                },
            ],
        }

        # UK major cities coordinates for distance calculation
        self.uk_postcodes = {
            "London": (51.5074, -0.1278),
            "Birmingham": (52.4862, -1.8904),
            "Manchester": (53.4808, -2.2426),
            "Leeds": (53.8008, -1.5491),
            "Glasgow": (55.8642, -4.2518),
            "Liverpool": (53.4084, -2.9916),
            "Bristol": (51.4545, -2.5879),
        }

    def find_providers(
        self,
        make: str,
        service_type: str,
        postcode: str,
        radius_miles: int = 25,
        include_tier1: bool = True,
        include_tier2: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find service providers for a specific make

        Args:
            make: Vehicle manufacturer
            service_type: Type of service needed
            postcode: Customer postcode
            radius_miles: Search radius in miles
            include_tier1: Include official dealers
            include_tier2: Include specialist independents

        Returns:
            List of providers sorted by rating and distance
        """
        providers = []
        customer_coords = self._postcode_to_coordinates(postcode)

        # Get Tier 1 providers
        if include_tier1:
            tier1_list = self.tier1_providers.get(make, [])
            for provider in tier1_list:
                provider_copy = provider.copy()
                provider_copy["distance_miles"] = self._calculate_distance(
                    customer_coords, provider["coordinates"]
                )

                # Calculate estimated cost
                base_cost = self._get_base_service_cost(service_type)
                provider_copy["estimated_cost"] = int(
                    base_cost * provider["cost_multiplier"]
                )

                # Only include if within radius
                if provider_copy["distance_miles"] <= radius_miles:
                    providers.append(provider_copy)

        # Get Tier 2 providers
        if include_tier2:
            tier2_list = self.tier2_providers.get(make, [])
            for provider in tier2_list:
                provider_copy = provider.copy()
                provider_copy["distance_miles"] = self._calculate_distance(
                    customer_coords, provider["coordinates"]
                )

                # Calculate estimated cost
                base_cost = self._get_base_service_cost(service_type)
                provider_copy["estimated_cost"] = int(
                    base_cost * provider["cost_multiplier"]
                )

                # Only include if within radius
                if provider_copy["distance_miles"] <= radius_miles:
                    providers.append(provider_copy)

        # Sort by rating (descending) and distance (ascending)
        providers.sort(key=lambda x: (-x["rating"], x["distance_miles"]))

        return providers

    def _postcode_to_coordinates(self, postcode: str) -> tuple:
        """
        Convert UK postcode to approximate coordinates
        In production, use proper postcode API (e.g., Postcodes.io)
        """
        # Extract postcode area (first letters)
        area = "".join([c for c in postcode if c.isalpha()])[:2].upper()

        # Simple mapping for demo (use real API in production)
        postcode_areas = {
            "SW": (51.4875, -0.1687),  # Southwest London
            "W1": (51.5145, -0.1527),  # West London
            "EC": (51.5155, -0.0922),  # East Central London
            "NW": (51.5430, -0.1755),  # Northwest London
            "SE": (51.4865, -0.0756),  # Southeast London
            "E1": (51.5157, -0.0703),  # East London
            "N1": (51.5416, -0.1022),  # North London
            "M1": (53.4808, -2.2426),  # Manchester
            "B1": (52.4862, -1.8904),  # Birmingham
            "LS": (53.8008, -1.5491),  # Leeds
            "L1": (53.4084, -2.9916),  # Liverpool
            "BS": (51.4545, -2.5879),  # Bristol
            "G1": (55.8642, -4.2518),  # Glasgow
        }

        return postcode_areas.get(area, (51.5074, -0.1278))  # Default to London

    def _calculate_distance(self, coords1: tuple, coords2: tuple) -> float:
        """
        Calculate distance between two coordinates in miles
        Using Haversine formula
        """
        lat1, lon1 = coords1
        lat2, lon2 = coords2

        # Radius of Earth in miles
        R = 3959

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return round(distance, 1)

    def _get_base_service_cost(self, service_type: str) -> int:
        """Get base cost for service type"""
        costs = {
            "scheduled_service": 500,
            "minor_service": 400,
            "major_service": 800,
            "repair": 600,
            "upgrade": 1500,
            "inspection": 150,
            "mot": 50,
            "brake_service": 800,
            "tire_service": 600,
        }
        return costs.get(service_type, 500)

    def get_provider_details(
        self, provider_name: str, make: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific provider"""
        # Search in Tier 1
        for provider in self.tier1_providers.get(make, []):
            if provider["name"].lower() == provider_name.lower():
                return provider

        # Search in Tier 2
        for provider in self.tier2_providers.get(make, []):
            if provider["name"].lower() == provider_name.lower():
                return provider

        return None


# Singleton instance
service_provider_aggregator = ServiceProviderAggregator()
