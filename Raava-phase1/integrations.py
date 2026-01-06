"""
Marketplace API Integration Module
Integrates with AutoTrader, CarGurus, and other luxury car marketplaces
"""

import requests
import os
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# ============= AutoTrader API Integration =============
class AutoTraderAPI:
    """AutoTrader UK API Integration"""

    def __init__(self):
        self.api_key = os.getenv("AUTOTRADER_API_KEY")
        self.base_url = "https://api.autotrader.co.uk/v1"
        self.timeout = 10

    def search_cars(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        postcode: Optional[str] = None,
        radius: int = 50,
    ) -> List[Dict]:
        """Search cars on AutoTrader"""
        try:
            params = {"api_key": self.api_key, "radius": radius, "sort_by": "relevance"}

            if make:
                params["make"] = make
            if model:
                params["model"] = model
            if min_price:
                params["minimum_price"] = min_price
            if max_price:
                params["maximum_price"] = max_price
            if min_year:
                params["minimum_year"] = min_year
            if max_year:
                params["maximum_year"] = max_year
            if postcode:
                params["postcode"] = postcode

            response = requests.get(
                f"{self.base_url}/search", params=params, timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_results(data, "autotrader")
            else:
                print(f"AutoTrader API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"AutoTrader search error: {e}")
            return []

    def _parse_results(self, data: Dict, source: str) -> List[Dict]:
        """Parse AutoTrader API response"""
        cars = []
        for listing in data.get("listings", []):
            car = {
                "id": listing.get("id"),
                "title": listing.get("title"),
                "make": listing.get("make"),
                "model": listing.get("model"),
                "year": listing.get("year"),
                "price": listing.get("price"),
                "mileage": listing.get("mileage"),
                "location": listing.get("location"),
                "seller_type": listing.get("seller_type", "dealer"),
                "description": listing.get("description"),
                "image_url": listing.get("image_url"),
                "url": listing.get("url"),
                "source": source,
                "seller_name": listing.get("seller_name"),
                "fetched_at": datetime.now().isoformat(),
            }
            cars.append(car)
        return cars


# ============= CarGurus API Integration =============
class CarGurusAPI:
    """CarGurus API Integration (US-based, limited international)"""

    def __init__(self):
        self.api_key = os.getenv("CARGURUS_API_KEY")
        self.base_url = "https://www.cargurus.com/api/v1"
        self.timeout = 10

    def search_cars(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_year: Optional[int] = None,
        location: Optional[str] = None,
    ) -> List[Dict]:
        """Search cars on CarGurus"""
        try:
            params = {"apikey": self.api_key, "limit": 50, "sortBy": "relevance"}

            if make:
                params["makes"] = make
            if model:
                params["models"] = model
            if min_price:
                params["minPrice"] = min_price
            if max_price:
                params["maxPrice"] = max_price
            if min_year:
                params["minYear"] = min_year
            if location:
                params["zipCode"] = location

            response = requests.get(
                f"{self.base_url}/vehicle", params=params, timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_results(data, "cargurus")
            else:
                print(f"CarGurus API error: {response.status_code}")
                return []

        except Exception as e:
            print(f"CarGurus search error: {e}")
            return []

    def _parse_results(self, data: Dict, source: str) -> List[Dict]:
        """Parse CarGurus response"""
        cars = []
        for listing in data.get("results", []):
            car = {
                "id": listing.get("gvwr_id"),
                "title": f"{listing.get('year')} {listing.get('make')} {listing.get('model')}",
                "make": listing.get("make"),
                "model": listing.get("model"),
                "year": listing.get("year"),
                "price": listing.get("price"),
                "mileage": listing.get("mileage"),
                "location": listing.get("location"),
                "seller_type": "dealer",
                "description": listing.get("description"),
                "image_url": listing.get("image_url"),
                "url": listing.get("listing_url"),
                "source": source,
                "dealer_name": listing.get("dealer_name"),
                "fetched_at": datetime.now().isoformat(),
            }
            cars.append(car)
        return cars


# ============= Manufacturer APIs =============
class FerrariAPI:
    """Ferrari Official Inventory (if available)"""

    def __init__(self):
        self.base_url = "https://www.ferrari.com/api/dealers"
        self.timeout = 10

    def search_inventory(self, model: Optional[str] = None) -> List[Dict]:
        """Search Ferrari inventory from authorized dealers"""
        try:
            # This would require Ferrari partnership/API access
            # Implementation depends on Ferrari's actual API
            return []
        except Exception as e:
            print(f"Ferrari API error: {e}")
            return []


class PorscheAPI:
    """Porsche Official Inventory Integration"""

    def __init__(self):
        self.base_url = "https://www.porsche.com/api/inventory"
        self.timeout = 10

    def search_inventory(self, model: Optional[str] = None) -> List[Dict]:
        """Search Porsche inventory"""
        try:
            # Implementation depends on Porsche API
            return []
        except Exception as e:
            print(f"Porsche API error: {e}")
            return []


# ============= Multi-Source Search Aggregator =============
class LuxuryCarAggregator:
    """Aggregates results from multiple marketplace APIs"""

    def __init__(self):
        self.autotrader = AutoTraderAPI()
        self.cargurus = CarGurusAPI()
        self.sources = {"autotrader": self.autotrader, "cargurus": self.cargurus}

    def search_all_marketplaces(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_year: Optional[int] = None,
        location: Optional[str] = None,
    ) -> Dict:
        """Search across all configured marketplaces"""
        results = {"total": 0, "by_source": {}, "cars": []}

        # Search AutoTrader
        print(f"Searching AutoTrader for {make} {model}...")
        at_results = self.autotrader.search_cars(
            make=make,
            model=model,
            min_price=min_price,
            max_price=max_price,
            min_year=min_year,
            postcode=location,
        )
        results["by_source"]["autotrader"] = len(at_results)
        results["cars"].extend(at_results)

        # Search CarGurus (US-only, skip if UK location)
        if location and not location.startswith("SW") and not location.startswith("SE"):
            print(f"Searching CarGurus for {make} {model}...")
            cg_results = self.cargurus.search_cars(
                make=make,
                model=model,
                min_price=min_price,
                max_price=max_price,
                min_year=min_year,
                location=location,
            )
            results["by_source"]["cargurus"] = len(cg_results)
            results["cars"].extend(cg_results)

        # Deduplicate and sort by price
        results["cars"] = self._deduplicate_and_sort(results["cars"])
        results["total"] = len(results["cars"])

        return results

    def _deduplicate_and_sort(self, cars: List[Dict]) -> List[Dict]:
        """Remove duplicates and sort by price"""
        seen = set()
        unique_cars = []

        for car in cars:
            # Create a signature to detect duplicates
            signature = (
                car.get("make", "").lower(),
                car.get("model", "").lower(),
                car.get("year"),
                car.get("price"),
                car.get("location", "").lower(),
            )

            if signature not in seen:
                seen.add(signature)
                unique_cars.append(car)

        # Sort by price (ascending)
        return sorted(unique_cars, key=lambda x: x.get("price", 0))


# ============= Helper Functions =============
def validate_api_keys() -> Dict[str, bool]:
    """Check if all necessary API keys are configured"""
    return {
        "autotrader": bool(os.getenv("AUTOTRADER_API_KEY")),
        "cargurus": bool(os.getenv("CARGURUS_API_KEY")),
    }


def format_search_results(cars: List[Dict], limit: int = 10) -> str:
    """Format search results for concierge response"""
    if not cars:
        return "I couldn't find any matching vehicles at the moment. Let me help you refine your search parameters."

    output = f"I found {len(cars)} vehicles matching your criteria. Here are the top {min(limit, len(cars))}:\n\n"

    for i, car in enumerate(cars[:limit], 1):
        output += f"{i}. **{car['year']} {car['make']} {car['model']}**\n"
        output += f"   Price: £{car['price']:,} | Mileage: {car['mileage']:,} miles\n"
        output += f"   Location: {car['location']} | Source: {car['source'].upper()}\n"
        if car.get("seller_name"):
            output += f"   Seller: {car['seller_name']}\n"
        output += "\n"

    return output
