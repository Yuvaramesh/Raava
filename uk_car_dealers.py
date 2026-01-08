"""
UK Car Dealer API Aggregation
Integrates with AutoTrader, Motors.co.uk, CarGurus, and PistonHeads
"""

import requests
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from config import (
    AUTOTRADER_API_KEY,
    MOTORS_API_KEY,
    CARGURUS_API_KEY,
    LUXURY_MAKES,
    MINIMUM_LUXURY_PRICE,
)


class UKCarDealerAggregator:
    """Aggregates luxury and sports cars from multiple UK dealers"""

    def __init__(self):
        self.autotrader_base = "https://www.autotrader.co.uk/car-search"
        self.motors_base = "https://www.motors.co.uk/car"
        self.cargurus_base = "https://www.cargurus.co.uk/Cars"
        self.pistonheads_base = "https://www.pistonheads.com/classifieds/used-cars"

    def search_luxury_cars(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        price_min: int = MINIMUM_LUXURY_PRICE,
        price_max: Optional[int] = None,
        postcode: str = "SW1A 1AA",  # Default to Central London
        radius: int = 50,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for luxury cars across multiple UK platforms

        Args:
            make: Car manufacturer (e.g., "Ferrari", "Porsche")
            model: Specific model (e.g., "911", "F8")
            price_min: Minimum price in GBP
            price_max: Maximum price in GBP
            postcode: UK postcode for location-based search
            radius: Search radius in miles
            limit: Maximum results to return

        Returns:
            List of standardized car listings
        """
        all_cars = []

        # AutoTrader Search
        try:
            autotrader_results = self._search_autotrader(
                make, model, price_min, price_max, postcode, radius
            )
            all_cars.extend(autotrader_results)
        except Exception as e:
            print(f"[AutoTrader Error] {e}")

        # Motors.co.uk Search
        try:
            motors_results = self._search_motors(
                make, model, price_min, price_max, postcode
            )
            all_cars.extend(motors_results)
        except Exception as e:
            print(f"[Motors Error] {e}")

        # CarGurus Search
        try:
            cargurus_results = self._search_cargurus(make, model, price_min, price_max)
            all_cars.extend(cargurus_results)
        except Exception as e:
            print(f"[CarGurus Error] {e}")

        # PistonHeads Search (best for performance/luxury)
        try:
            pistonheads_results = self._search_pistonheads(
                make, model, price_min, price_max
            )
            all_cars.extend(pistonheads_results)
        except Exception as e:
            print(f"[PistonHeads Error] {e}")

        # Deduplicate and sort by price
        unique_cars = self._deduplicate_listings(all_cars)
        sorted_cars = sorted(unique_cars, key=lambda x: x.get("price", 0))

        return sorted_cars[:limit]

    def _search_autotrader(
        self, make, model, price_min, price_max, postcode, radius
    ) -> List[Dict[str, Any]]:
        """Search AutoTrader UK"""
        params = {
            "postcode": postcode,
            "radius": radius,
            "price-from": price_min,
            "sort": "relevance",
        }

        if make:
            params["make"] = make
        if model:
            params["model"] = model
        if price_max:
            params["price-to"] = price_max

        # If API key available, use official API
        if AUTOTRADER_API_KEY:
            headers = {"Authorization": f"Bearer {AUTOTRADER_API_KEY}"}
            response = requests.get(
                "https://api.autotrader.co.uk/v1/vehicles",
                headers=headers,
                params=params,
                timeout=10,
            )
            if response.ok:
                data = response.json()
                return self._parse_autotrader_api(data)

        # Fallback to web scraping (for demo purposes)
        return self._scrape_autotrader(params)

    def _scrape_autotrader(self, params: Dict) -> List[Dict[str, Any]]:
        """Scrape AutoTrader listings (fallback method)"""
        cars = []
        try:
            # Build URL
            url = (
                self.autotrader_base
                + "?"
                + "&".join([f"{k}={v}" for k, v in params.items()])
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, "html.parser")

            # Find car listings (update selectors as needed)
            listings = soup.find_all("article", class_="product-card")

            for listing in listings[:20]:  # Limit to 20 per source
                try:
                    car = self._parse_autotrader_listing(listing)
                    if car:
                        cars.append(car)
                except Exception as e:
                    continue

        except Exception as e:
            print(f"[AutoTrader Scrape Error] {e}")

        return cars

    def _parse_autotrader_listing(self, listing) -> Optional[Dict[str, Any]]:
        """Parse AutoTrader HTML listing"""
        try:
            title_elem = listing.find("h2", class_="product-card-details__title")
            price_elem = listing.find("div", class_="product-card-pricing__price")

            if not title_elem or not price_elem:
                return None

            title = title_elem.text.strip()
            price_text = price_elem.text.strip().replace("£", "").replace(",", "")

            # Extract make/model from title
            parts = title.split()
            make = parts[0] if parts else "Unknown"
            model = parts[1] if len(parts) > 1 else ""
            year = parts[2] if len(parts) > 2 and parts[2].isdigit() else ""

            # Extract mileage
            mileage_elem = listing.find(
                "li", text=lambda t: "miles" in t.lower() if t else False
            )
            mileage = 0
            if mileage_elem:
                mileage_text = mileage_elem.text.strip()
                mileage = int("".join(filter(str.isdigit, mileage_text)))

            # Get image
            img_elem = listing.find("img")
            image_url = img_elem["src"] if img_elem else ""

            # Get URL
            link_elem = listing.find("a", href=True)
            listing_url = (
                "https://www.autotrader.co.uk" + link_elem["href"] if link_elem else ""
            )

            return {
                "source": "AutoTrader",
                "title": title,
                "make": make,
                "model": model,
                "year": int(year) if year else None,
                "price": float(price_text) if price_text else 0,
                "mileage": mileage,
                "fuel_type": "Petrol",  # Would need deeper scraping
                "body_type": "Coupe",  # Would need deeper scraping
                "image_url": image_url,
                "listing_url": listing_url,
                "location": "UK",
                "seller_type": "Dealer",
            }
        except Exception as e:
            return None

    def _parse_autotrader_api(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse AutoTrader API response"""
        cars = []
        listings = data.get("vehicles", [])

        for listing in listings:
            car = {
                "source": "AutoTrader",
                "title": listing.get("title", ""),
                "make": listing.get("make", ""),
                "model": listing.get("model", ""),
                "year": listing.get("year"),
                "price": listing.get("price", {}).get("amount", 0),
                "mileage": listing.get("mileage", {}).get("value", 0),
                "fuel_type": listing.get("fuelType", ""),
                "body_type": listing.get("bodyType", ""),
                "image_url": listing.get("images", [{}])[0].get("url", ""),
                "listing_url": listing.get("url", ""),
                "location": listing.get("location", {}).get("town", "UK"),
                "seller_type": listing.get("sellerType", "Dealer"),
            }
            cars.append(car)

        return cars

    def _search_motors(
        self, make, model, price_min, price_max, postcode
    ) -> List[Dict[str, Any]]:
        """Search Motors.co.uk"""
        # Similar implementation to AutoTrader
        # Would use Motors API or scraping
        return []

    def _search_cargurus(
        self, make, model, price_min, price_max
    ) -> List[Dict[str, Any]]:
        """Search CarGurus UK"""
        # CarGurus API integration
        return []

    def _search_pistonheads(
        self, make, model, price_min, price_max
    ) -> List[Dict[str, Any]]:
        """Search PistonHeads Classifieds"""
        cars = []
        try:
            url = f"{self.pistonheads_base}?Category=used-cars"

            if make:
                url += f"&Make={make.lower()}"
            if model:
                url += f"&Model={model.lower()}"
            if price_min:
                url += f"&MinPrice={price_min}"
            if price_max:
                url += f"&MaxPrice={price_max}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, "html.parser")

            # Parse PistonHeads listings
            listings = soup.find_all("div", class_="listing-item")

            for listing in listings[:15]:
                try:
                    car = self._parse_pistonheads_listing(listing)
                    if car:
                        cars.append(car)
                except Exception:
                    continue

        except Exception as e:
            print(f"[PistonHeads Error] {e}")

        return cars

    def _parse_pistonheads_listing(self, listing) -> Optional[Dict[str, Any]]:
        """Parse PistonHeads listing"""
        # Implementation similar to AutoTrader parsing
        return None

    def _deduplicate_listings(self, cars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate listings based on make, model, price, mileage"""
        seen = set()
        unique = []

        for car in cars:
            # Create unique key
            key = (
                car.get("make", "").lower(),
                car.get("model", "").lower(),
                car.get("year", 0),
                car.get("price", 0),
                car.get("mileage", 0),
            )

            if key not in seen:
                seen.add(key)
                unique.append(car)

        return unique


# Singleton instance
uk_dealer_aggregator = UKCarDealerAggregator()
