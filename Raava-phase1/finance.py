"""
Finance Calculation Models for Luxury Vehicle Financing
Supports: PCP, HP, Lease, and Bespoke financing structures
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math


@dataclass
class FinanceQuote:
    """Represents a finance quote"""

    product_name: str
    annual_rate: float
    monthly_payment: float
    total_cost: float
    term_months: int
    deposit: float
    final_payment: Optional[float]
    total_interest: float
    provider: str
    rating: float
    key_features: list


# ============= Base Finance Calculator =============
class FinanceCalculator:
    """Base class for finance calculations"""

    @staticmethod
    def calculate_monthly_payment(
        principal: float, annual_rate: float, months: int
    ) -> float:
        """Calculate monthly payment using standard amortization formula"""
        if annual_rate == 0:
            return principal / months

        monthly_rate = annual_rate / 12 / 100
        numerator = principal * monthly_rate * (1 + monthly_rate) ** months
        denominator = (1 + monthly_rate) ** months - 1
        return numerator / denominator

    @staticmethod
    def calculate_total_interest(
        monthly_payment: float, months: int, principal: float
    ) -> float:
        """Calculate total interest paid"""
        return (monthly_payment * months) - principal

    @staticmethod
    def calculate_apr(monthly_rate: float) -> float:
        """Convert monthly rate to APR"""
        return (monthly_rate * 12) * 100


# ============= HP (Hire Purchase) =============
class HPCalculator(FinanceCalculator):
    """Hire Purchase Finance Calculator"""

    @staticmethod
    def calculate(
        vehicle_price: float,
        deposit_percent: float = 20,
        annual_rate: float = 4.9,
        term_months: int = 60,
    ) -> FinanceQuote:
        """
        Calculate HP quote

        Args:
            vehicle_price: Price of vehicle
            deposit_percent: Deposit as % of price (20-50% typical)
            annual_rate: Annual interest rate (typically 3.9-7.9%)
            term_months: Finance term in months (typically 36-60)
        """
        deposit = vehicle_price * (deposit_percent / 100)
        amount_to_finance = vehicle_price - deposit

        monthly_payment = HPCalculator.calculate_monthly_payment(
            amount_to_finance, annual_rate, term_months
        )

        total_paid = (monthly_payment * term_months) + deposit
        total_interest = total_paid - vehicle_price

        return FinanceQuote(
            product_name="Hire Purchase",
            annual_rate=annual_rate,
            monthly_payment=monthly_payment,
            total_cost=total_paid,
            term_months=term_months,
            deposit=deposit,
            final_payment=None,
            total_interest=total_interest,
            provider="Multiple",
            rating=4.2,
            key_features=[
                "Own the car at end of term",
                "Fixed monthly payments",
                "No mileage restrictions",
                "Full maintenance flexibility",
            ],
        )


# ============= PCP (Personal Contract Purchase) =============
class PCPCalculator(FinanceCalculator):
    """Personal Contract Purchase Finance Calculator"""

    @staticmethod
    def calculate(
        vehicle_price: float,
        residual_value_percent: float = 50,
        annual_rate: float = 3.9,
        term_months: int = 36,
        annual_mileage: int = 10000,
    ) -> FinanceQuote:
        """
        Calculate PCP quote

        Args:
            vehicle_price: Price of vehicle
            residual_value_percent: Estimated residual value at end (typically 45-60%)
            annual_rate: APR (typically 2.9-5.9%)
            term_months: Contract length (typically 24-48 months)
            annual_mileage: Expected annual mileage
        """
        deposit = vehicle_price * 0.20  # Typical 20% deposit
        residual_value = vehicle_price * (residual_value_percent / 100)
        amount_to_depreciate = vehicle_price - residual_value

        # Calculate monthly depreciation charge
        monthly_depreciation = amount_to_depreciate / term_months

        # Calculate interest charge on outstanding amount
        monthly_interest = (vehicle_price - deposit) * (annual_rate / 100) / 12

        monthly_payment = monthly_depreciation + monthly_interest
        total_monthly_payments = monthly_payment * term_months
        total_cost = deposit + total_monthly_payments

        return FinanceQuote(
            product_name="Personal Contract Purchase",
            annual_rate=annual_rate,
            monthly_payment=monthly_payment,
            total_cost=total_cost,
            term_months=term_months,
            deposit=deposit,
            final_payment=residual_value,
            total_interest=0,  # Interest built into monthly calc
            provider="Multiple",
            rating=4.7,
            key_features=[
                f"Mileage limit: {annual_mileage * (term_months // 12):,} miles",
                "Return the car at end of term (no residual risk)",
                "Lower monthly payments than HP",
                "Warranty typically included",
            ],
        )


# ============= Lease Calculator =============
class LeaseCalculator(FinanceCalculator):
    """Car Lease Calculator"""

    @staticmethod
    def calculate(
        vehicle_price: float,
        residual_value_percent: float = 40,
        annual_rate: float = 2.9,
        term_months: int = 36,
        annual_mileage: int = 12000,
        excess_mileage_cost: float = 0.35,
    ) -> FinanceQuote:
        """
        Calculate lease quote

        Args:
            vehicle_price: Vehicle price/value
            residual_value_percent: Residual value % (typically 35-50%)
            annual_rate: Money factor (APR equivalent)
            term_months: Lease length (typically 24-48 months)
            annual_mileage: Allowed annual mileage
            excess_mileage_cost: Cost per excess mile
        """
        residual_value = vehicle_price * (residual_value_percent / 100)

        # Calculate depreciation
        monthly_depreciation = (vehicle_price - residual_value) / term_months

        # Calculate "rent charge" (interest equivalent)
        money_factor = annual_rate / 100 / 12
        rent_charge = money_factor * (vehicle_price + residual_value)

        monthly_payment = monthly_depreciation + rent_charge
        total_payments = monthly_payment * term_months
        total_cost = total_payments

        return FinanceQuote(
            product_name="Car Lease",
            annual_rate=annual_rate,
            monthly_payment=monthly_payment,
            total_cost=total_cost,
            term_months=term_months,
            deposit=vehicle_price * 0.10,  # Typical cap reduction
            final_payment=None,
            total_interest=0,
            provider="Lease Company",
            rating=4.5,
            key_features=[
                f"Annual mileage: {annual_mileage:,} miles",
                f"Excess mileage: £{excess_mileage_cost:.2f}/mile",
                "Warranty included",
                "Maintenance typically included",
                "No residual value risk",
                "Return at end of term",
            ],
        )


# ============= Bespoke Finance (UHNW) =============
class BespokeFinanceCalculator(FinanceCalculator):
    """Bespoke Finance for Ultra-High-Net-Worth Individuals"""

    @staticmethod
    def calculate(
        vehicle_price: float,
        annual_rate: float = 1.9,
        term_months: int = 60,
        custom_structure: Optional[Dict] = None,
    ) -> FinanceQuote:
        """
        Calculate bespoke finance quote

        Typical for UHNW: low rates, flexible terms, customizable structure
        """
        if not custom_structure:
            custom_structure = {
                "deposit_percent": 25,
                "balloon_payment_percent": 0,
                "grace_period_months": 0,
            }

        deposit = vehicle_price * (custom_structure["deposit_percent"] / 100)
        balloon = vehicle_price * (custom_structure["balloon_payment_percent"] / 100)
        amount_to_finance = vehicle_price - deposit - balloon

        monthly_payment = BespokeFinanceCalculator.calculate_monthly_payment(
            amount_to_finance, annual_rate, term_months
        )

        total_cost = deposit + (monthly_payment * term_months) + balloon
        total_interest = BespokeFinanceCalculator.calculate_total_interest(
            monthly_payment, term_months, amount_to_finance
        )

        return FinanceQuote(
            product_name="Bespoke Finance",
            annual_rate=annual_rate,
            monthly_payment=monthly_payment,
            total_cost=total_cost,
            term_months=term_months,
            deposit=deposit,
            final_payment=balloon if balloon > 0 else None,
            total_interest=total_interest,
            provider="Premium Finance Provider",
            rating=4.8,
            key_features=[
                "Ultra-low interest rates",
                "Flexible payment structures",
                "No mileage restrictions",
                "Customizable terms",
                "Dedicated relationship manager",
                "International coverage available",
            ],
        )


# ============= Finance Quote Comparison =============
class FinanceComparator:
    """Compare different finance options"""

    @staticmethod
    def compare_all_options(
        vehicle_price: float, annual_mileage: int = 10000, term_months: int = 36
    ) -> Dict[str, FinanceQuote]:
        """Generate quotes for all finance types"""

        quotes = {
            "hp": HPCalculator.calculate(
                vehicle_price=vehicle_price, term_months=term_months
            ),
            "pcp": PCPCalculator.calculate(
                vehicle_price=vehicle_price,
                term_months=term_months,
                annual_mileage=annual_mileage,
            ),
            "lease": LeaseCalculator.calculate(
                vehicle_price=vehicle_price,
                term_months=term_months,
                annual_mileage=annual_mileage,
            ),
            "bespoke": BespokeFinanceCalculator.calculate(
                vehicle_price=vehicle_price, term_months=term_months
            ),
        }

        return quotes

    @staticmethod
    def format_comparison(quotes: Dict[str, FinanceQuote]) -> str:
        """Format quotes for display"""
        output = "**Finance Options Comparison**\n\n"

        for option_name, quote in quotes.items():
            output += f"**{quote.product_name}** (Rating: ⭐ {quote.rating}/5)\n"
            output += f"  Monthly Payment: £{quote.monthly_payment:,.2f}\n"
            output += f"  Deposit: £{quote.deposit:,.2f}\n"
            output += f"  APR: {quote.annual_rate}%\n"
            output += f"  Term: {quote.term_months} months\n"
            output += f"  Total Cost: £{quote.total_cost:,.2f}\n"
            output += f"  Features: {', '.join(quote.key_features[:2])}\n\n"

        return output


# ============= Insurance Cost Estimation =============
class InsuranceEstimator:
    """Estimate insurance costs for luxury vehicles"""

    INSURANCE_RATES = {
        "Ferrari": {"base_annual_percent": 0.035, "rating": 4.8},
        "Lamborghini": {"base_annual_percent": 0.032, "rating": 4.7},
        "Porsche": {"base_annual_percent": 0.025, "rating": 4.6},
        "McLaren": {"base_annual_percent": 0.038, "rating": 4.8},
        "Aston Martin": {"base_annual_percent": 0.028, "rating": 4.5},
    }

    @staticmethod
    def estimate_annual_insurance(
        make: str,
        vehicle_price: float,
        driver_age: int = 45,
        years_experience: int = 20,
        claims_history: int = 0,
    ) -> Dict:
        """Estimate annual insurance cost"""

        base_rate = InsuranceEstimator.INSURANCE_RATES.get(
            make, {"base_annual_percent": 0.03, "rating": 4.5}
        )

        base_cost = vehicle_price * base_rate["base_annual_percent"]

        # Age factor (younger = higher)
        age_factor = 1.0
        if driver_age < 25:
            age_factor = 1.8
        elif driver_age < 30:
            age_factor = 1.5
        elif driver_age < 35:
            age_factor = 1.2

        # Experience factor
        exp_factor = max(0.7, 1.0 - (years_experience * 0.02))

        # Claims factor
        claims_factor = 1.0 + (claims_history * 0.15)

        final_cost = base_cost * age_factor * exp_factor * claims_factor
        monthly_cost = final_cost / 12

        return {
            "annual_cost": round(final_cost, 2),
            "monthly_cost": round(monthly_cost, 2),
            "base_rate_percent": base_rate["base_annual_percent"] * 100,
            "factors_applied": {
                "age": f"{age_factor:.2f}x",
                "experience": f"{exp_factor:.2f}x",
                "claims": f"{claims_factor:.2f}x",
            },
            "providers": {
                "Hiscox": final_cost * 0.95,  # Specialist insurer
                "Allianz": final_cost,
                "Lemonade": final_cost * 1.05,
            },
        }
