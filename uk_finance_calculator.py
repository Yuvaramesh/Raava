"""
UK Car Finance Calculator
Integrates with Zuto, Santander, Black Horse, and other UK finance providers
"""

import requests
from typing import Dict, List, Optional, Any
from config import (
    ZUTO_PARTNER_ID,
    SANTANDER_API_KEY,
    BLACK_HORSE_API_KEY,
    DEFAULT_DEPOSIT_PERCENTAGE,
    DEFAULT_LOAN_TERM_MONTHS,
    DEFAULT_APR,
)


class UKFinanceCalculator:
    """Calculate and compare car finance options from UK providers"""

    def __init__(self):
        self.providers = {
            "Zuto": {"apr": 9.9, "max_term": 60, "min_deposit": 10},
            "Santander Consumer": {"apr": 8.9, "max_term": 60, "min_deposit": 10},
            "Black Horse": {"apr": 9.4, "max_term": 60, "min_deposit": 10},
            "Close Brothers": {"apr": 10.2, "max_term": 48, "min_deposit": 15},
            "MotoNovo": {"apr": 9.7, "max_term": 60, "min_deposit": 10},
        }

    def calculate_all_options(
        self,
        vehicle_price: float,
        deposit_percent: float = DEFAULT_DEPOSIT_PERCENTAGE,
        term_months: int = DEFAULT_LOAN_TERM_MONTHS,
        credit_score: str = "Good",  # Excellent, Good, Fair, Poor
    ) -> Dict[str, Any]:
        """
        Calculate finance options across all providers

        Args:
            vehicle_price: Total vehicle price in GBP
            deposit_percent: Deposit as percentage of price
            term_months: Loan term in months (12, 24, 36, 48, 60)
            credit_score: Credit rating category

        Returns:
            Dictionary with PCP, HP, and Lease options from all providers
        """
        deposit_amount = vehicle_price * (deposit_percent / 100)
        loan_amount = vehicle_price - deposit_amount

        results = {
            "vehicle_price": vehicle_price,
            "deposit_amount": deposit_amount,
            "loan_amount": loan_amount,
            "term_months": term_months,
            "credit_score": credit_score,
            "pcp_options": [],
            "hp_options": [],
            "lease_options": [],
        }

        # Calculate for each provider
        for provider, details in self.providers.items():
            # Adjust APR based on credit score
            adjusted_apr = self._adjust_apr_for_credit(details["apr"], credit_score)

            # PCP (Personal Contract Purchase)
            pcp = self._calculate_pcp(
                loan_amount, term_months, adjusted_apr, vehicle_price, provider
            )
            results["pcp_options"].append(pcp)

            # HP (Hire Purchase)
            hp = self._calculate_hp(loan_amount, term_months, adjusted_apr, provider)
            results["hp_options"].append(hp)

            # Lease (PCH - Personal Contract Hire)
            lease = self._calculate_lease(
                vehicle_price, term_months, adjusted_apr, provider
            )
            results["lease_options"].append(lease)

        # Sort by monthly payment
        results["pcp_options"].sort(key=lambda x: x["monthly_payment"])
        results["hp_options"].sort(key=lambda x: x["monthly_payment"])
        results["lease_options"].sort(key=lambda x: x["monthly_payment"])

        # Add best deal recommendation
        results["recommended"] = self._determine_best_option(results)

        return results

    def _calculate_pcp(
        self,
        loan_amount: float,
        term: int,
        apr: float,
        vehicle_price: float,
        provider: str,
    ) -> Dict[str, Any]:
        """
        Calculate PCP (Personal Contract Purchase)
        Lower monthly payments, optional final balloon payment
        """
        # PCP typically finances 50-60% of vehicle value
        # Final balloon payment (GMFV) is ~30-40% of vehicle price
        gmfv_percent = 35  # Guaranteed Minimum Future Value
        gmfv = vehicle_price * (gmfv_percent / 100)

        # Amount to finance (excluding balloon)
        pcp_loan_amount = loan_amount - gmfv

        # Monthly interest rate
        monthly_rate = (apr / 100) / 12

        # Calculate monthly payment
        if monthly_rate > 0:
            monthly_payment = (
                pcp_loan_amount
                * (monthly_rate * (1 + monthly_rate) ** term)
                / (((1 + monthly_rate) ** term) - 1)
            )
        else:
            monthly_payment = pcp_loan_amount / term

        total_payments = monthly_payment * term
        total_cost = total_payments + gmfv
        total_interest = total_cost - loan_amount

        return {
            "provider": provider,
            "type": "PCP",
            "monthly_payment": round(monthly_payment, 2),
            "balloon_payment": round(gmfv, 2),
            "total_payments": round(total_payments, 2),
            "total_cost": round(total_cost, 2),
            "total_interest": round(total_interest, 2),
            "apr": apr,
            "term_months": term,
            "description": f"Lower monthly payments. At end: pay £{gmfv:,.0f} to own, return car, or part-exchange",
        }

    def _calculate_hp(
        self, loan_amount: float, term: int, apr: float, provider: str
    ) -> Dict[str, Any]:
        """
        Calculate HP (Hire Purchase)
        Fixed monthly payments until car is owned
        """
        monthly_rate = (apr / 100) / 12

        if monthly_rate > 0:
            monthly_payment = (
                loan_amount
                * (monthly_rate * (1 + monthly_rate) ** term)
                / (((1 + monthly_rate) ** term) - 1)
            )
        else:
            monthly_payment = loan_amount / term

        total_payments = monthly_payment * term
        total_interest = total_payments - loan_amount

        return {
            "provider": provider,
            "type": "HP",
            "monthly_payment": round(monthly_payment, 2),
            "balloon_payment": 0,
            "total_payments": round(total_payments, 2),
            "total_cost": round(total_payments, 2),
            "total_interest": round(total_interest, 2),
            "apr": apr,
            "term_months": term,
            "description": f"Fixed payments. Own the car outright at end of term",
        }

    def _calculate_lease(
        self, vehicle_price: float, term: int, apr: float, provider: str
    ) -> Dict[str, Any]:
        """
        Calculate Lease (Personal Contract Hire)
        Never own the car, return at end
        """
        # Lease typically 0.8-1.2% of vehicle value per month
        lease_rate_percent = 1.0
        monthly_payment = vehicle_price * (lease_rate_percent / 100)

        total_payments = monthly_payment * term

        return {
            "provider": provider,
            "type": "Lease (PCH)",
            "monthly_payment": round(monthly_payment, 2),
            "balloon_payment": 0,
            "total_payments": round(total_payments, 2),
            "total_cost": round(total_payments, 2),
            "total_interest": 0,
            "apr": 0,
            "term_months": term,
            "description": "Never own the car. Return at end. Often includes maintenance",
        }

    def _adjust_apr_for_credit(self, base_apr: float, credit_score: str) -> float:
        """Adjust APR based on credit score"""
        adjustments = {
            "Excellent": -1.0,  # 1% reduction
            "Good": 0.0,  # No change
            "Fair": 2.0,  # 2% increase
            "Poor": 5.0,  # 5% increase
        }

        adjustment = adjustments.get(credit_score, 0.0)
        return max(4.9, base_apr + adjustment)  # Minimum 4.9% APR

    def _determine_best_option(self, results: Dict) -> Dict[str, str]:
        """Determine best finance option based on criteria"""
        recommendations = {}

        # Lowest monthly payment
        if results["pcp_options"]:
            best_pcp = results["pcp_options"][0]
            recommendations["lowest_monthly"] = (
                f"{best_pcp['provider']} PCP at £{best_pcp['monthly_payment']:,.2f}/month"
            )

        # Best for ownership (HP with lowest total cost)
        if results["hp_options"]:
            best_hp = min(results["hp_options"], key=lambda x: x["total_cost"])
            recommendations["best_ownership"] = (
                f"{best_hp['provider']} HP at £{best_hp['monthly_payment']:,.2f}/month "
                + f"(Total: £{best_hp['total_cost']:,.2f})"
            )

        # Most flexible (PCP with best terms)
        if results["pcp_options"]:
            best_flexible = results["pcp_options"][0]
            recommendations["most_flexible"] = (
                f"{best_flexible['provider']} PCP - "
                + f"£{best_flexible['monthly_payment']:,.2f}/month + "
                + f"£{best_flexible['balloon_payment']:,.2f} optional final payment"
            )

        return recommendations

    def get_zuto_quote(
        self, vehicle_price: float, deposit_amount: float, term_months: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote from Zuto API
        Requires partnership agreement with Zuto
        """
        if not ZUTO_PARTNER_ID:
            return None

        try:
            # Zuto API endpoint (example - check actual documentation)
            url = "https://api.zuto.com/v1/quote"

            payload = {
                "partner_id": ZUTO_PARTNER_ID,
                "vehicle_price": vehicle_price,
                "deposit": deposit_amount,
                "term_months": term_months,
                "product_type": "PCP",
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.ok:
                data = response.json()
                return {
                    "provider": "Zuto",
                    "monthly_payment": data.get("monthly_payment"),
                    "apr": data.get("apr"),
                    "total_cost": data.get("total_amount_payable"),
                    "quote_reference": data.get("quote_id"),
                }
        except Exception as e:
            print(f"[Zuto API Error] {e}")

        return None

    def format_finance_summary(self, options: Dict[str, Any]) -> str:
        """Format finance options for display to user"""
        summary = f"""
💰 **Finance Options for £{options['vehicle_price']:,.2f} Vehicle**

**Deposit:** £{options['deposit_amount']:,.2f} ({(options['deposit_amount']/options['vehicle_price']*100):.0f}%)
**Amount to Finance:** £{options['loan_amount']:,.2f}
**Term:** {options['term_months']} months

---

**🎯 RECOMMENDED OPTIONS:**
"""

        for key, value in options["recommended"].items():
            summary += f"\n• {key.replace('_', ' ').title()}: {value}"

        summary += "\n\n---\n\n**📊 PCP (Personal Contract Purchase) - Lowest Monthly Payments:**\n"

        for pcp in options["pcp_options"][:3]:
            summary += f"""
**{pcp['provider']}**
• Monthly: £{pcp['monthly_payment']:,.2f}
• Optional Final Payment: £{pcp['balloon_payment']:,.2f}
• APR: {pcp['apr']}%
• {pcp['description']}
"""

        summary += "\n**💪 HP (Hire Purchase) - Own the Car:**\n"

        for hp in options["hp_options"][:3]:
            summary += f"""
**{hp['provider']}**
• Monthly: £{hp['monthly_payment']:,.2f}
• Total Cost: £{hp['total_cost']:,.2f}
• APR: {hp['apr']}%
• {hp['description']}
"""

        return summary


# Singleton instance
uk_finance_calculator = UKFinanceCalculator()
