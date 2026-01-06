import os
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class FinanceType(Enum):
    """Finance product types"""

    HP = "Hire Purchase"
    PCP = "Personal Contract Purchase"
    PERSONAL_LOAN = "Personal Loan"
    LEASE = "Lease"


class CreditRating(Enum):
    """UK credit rating bands"""

    EXCELLENT = (0.09, "Excellent (740+)")
    GOOD = (0.11, "Good (670-739)")
    FAIR = (0.14, "Fair (580-669)")
    POOR = (0.17, "Poor (< 580)")

    def get_apr(self):
        return self.value[0]

    def get_label(self):
        return self.value[1]


@dataclass
class FinanceProvider:
    """UK Finance Provider"""

    name: str
    type: str
    apr_range: tuple  # (min, max)
    min_loan: int
    max_loan: int
    min_term: int  # months
    max_term: int  # months
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None


class FinanceProvidersService:
    """
    Manages integration with UK car finance providers.
    Currently supports Zuto API and generic provider data.
    """

    def __init__(self):
        self.providers = self._initialize_providers()

    def _initialize_providers(self) -> List[FinanceProvider]:
        """Initialize UK car finance providers"""
        return [
            FinanceProvider(
                name="Zuto",
                type="Multi-Product Aggregator",
                apr_range=(0.09, 0.19),
                min_loan=2000,
                max_loan=50000,
                min_term=12,
                max_term=60,
                api_endpoint="https://api.zuto.com",  # Placeholder
                api_key=os.getenv("ZUTO_API_KEY"),
            ),
            FinanceProvider(
                name="Upstart",
                type="AI-Powered Lending",
                apr_range=(0.08, 0.20),
                min_loan=1000,
                max_loan=75000,
                min_term=12,
                max_term=84,
                api_endpoint="https://api.upstart.com",  # Placeholder
                api_key=os.getenv("UPSTART_API_KEY"),
            ),
            FinanceProvider(
                name="Santander Motor Finance",
                type="Bank Direct",
                apr_range=(0.10, 0.18),
                min_loan=5000,
                max_loan=50000,
                min_term=12,
                max_term=60,
            ),
            FinanceProvider(
                name="Barclays Car Finance",
                type="Bank Direct",
                apr_range=(0.11, 0.19),
                min_loan=3000,
                max_loan=45000,
                min_term=12,
                max_term=60,
            ),
            FinanceProvider(
                name="Close Brothers Motor Finance",
                type="Specialist Lender",
                apr_range=(0.09, 0.17),
                min_loan=5000,
                max_loan=60000,
                min_term=12,
                max_term=60,
            ),
            FinanceProvider(
                name="BMW Financial Services",
                type="Manufacturer Finance",
                apr_range=(0.00, 0.12),  # Often 0% promotional rates
                min_loan=10000,
                max_loan=100000,
                min_term=12,
                max_term=84,
            ),
            FinanceProvider(
                name="Mercedes-Benz Finance",
                type="Manufacturer Finance",
                apr_range=(0.00, 0.12),
                min_loan=10000,
                max_loan=100000,
                min_term=12,
                max_term=84,
            ),
            FinanceProvider(
                name="Lamborghini Financial Services",
                type="Manufacturer Finance",
                apr_range=(0.02, 0.10),
                min_loan=50000,
                max_loan=200000,
                min_term=12,
                max_term=84,
            ),
        ]

    def get_providers(self, finance_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available finance providers, optionally filtered by type"""
        providers = [
            {
                "name": p.name,
                "type": p.type,
                "apr_range": p.apr_range,
                "min_loan": p.min_loan,
                "max_loan": p.max_loan,
                "terms": f"{p.min_term}-{p.max_term} months",
            }
            for p in self.providers
        ]

        if finance_type:
            providers = [
                p for p in providers if finance_type.lower() in p["type"].lower()
            ]

        return providers

    def get_best_rates(self, amount: int, term_months: int) -> List[Dict[str, Any]]:
        """Get best rates for a specific loan amount and term"""
        suitable_providers = [
            p
            for p in self.providers
            if p.min_loan <= amount <= p.max_loan
            and p.min_term <= term_months <= p.max_term
        ]

        # Sort by APR range (lower is better)
        suitable_providers.sort(key=lambda x: x.apr_range[1])

        return [
            {
                "name": p.name,
                "type": p.type,
                "apr_range": f"{p.apr_range[0]:.1%} - {p.apr_range[1]:.1%}",
                "min_rate": f"{p.apr_range[0]:.1%}",
                "max_rate": f"{p.apr_range[1]:.1%}",
            }
            for p in suitable_providers[:5]  # Top 5 suitable providers
        ]

    def query_zuto_finance(
        self, amount: int, term_months: int, credit_rating: str
    ) -> Dict[str, Any]:
        """Query Zuto finance calculator"""
        # This would call the actual Zuto API if available
        # For now, return calculated estimate
        zuto = next((p for p in self.providers if p.name == "Zuto"), None)
        if not zuto:
            return {}

        apr = self._get_apr_for_rating(credit_rating)
        monthly_payment = self._calculate_monthly_payment(amount, apr, term_months)

        return {
            "provider": "Zuto",
            "amount": amount,
            "apr": f"{apr:.2%}",
            "term_months": term_months,
            "monthly_payment": f"£{monthly_payment:.2f}",
            "total_repayment": f"£{monthly_payment * term_months:.2f}",
            "total_interest": f"£{(monthly_payment * term_months) - amount:.2f}",
        }

    def _get_apr_for_rating(self, credit_rating: str) -> float:
        """Get APR based on credit rating"""
        try:
            rating = CreditRating[credit_rating.upper().replace(" ", "_")]
            return rating.get_apr()
        except KeyError:
            return 0.14  # Default to Fair rating

    def _calculate_monthly_payment(
        self, principal: int, apr: float, months: int
    ) -> float:
        """Calculate monthly payment using standard formula"""
        if apr == 0:
            return principal / months

        monthly_rate = apr / 12
        payment = (
            principal
            * (monthly_rate * (1 + monthly_rate) ** months)
            / ((1 + monthly_rate) ** months - 1)
        )
        return payment
