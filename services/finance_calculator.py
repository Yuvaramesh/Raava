from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


@dataclass
class FinanceCalculation:
    """Finance calculation result"""

    vehicle_price: int
    deposit: int
    loan_amount: int
    apr: float
    term_months: int
    monthly_payment: float
    total_interest: float
    total_repayment: float


class FinanceCalculator:
    """
    Finance calculator based on Zuto methodology.
    Supports HP, PCP, and Personal Loans.
    """

    @staticmethod
    def calculate_hp(
        vehicle_price: int,
        deposit: int,
        apr: float,
        term_months: int,
    ) -> FinanceCalculation:
        """
        Calculate Hire Purchase (HP) finance.
        - Regular monthly payments
        - Finance secured against vehicle
        - No balloon fee at end
        """
        loan_amount = vehicle_price - deposit

        if apr == 0:
            monthly_payment = loan_amount / term_months
            total_interest = 0
        else:
            monthly_rate = apr / 12
            numerator = monthly_rate * (1 + monthly_rate) ** term_months
            denominator = (1 + monthly_rate) ** term_months - 1
            monthly_payment = loan_amount * (numerator / denominator)
            total_interest = (monthly_payment * term_months) - loan_amount

        total_repayment = monthly_payment * term_months

        return FinanceCalculation(
            vehicle_price=vehicle_price,
            deposit=deposit,
            loan_amount=loan_amount,
            apr=apr,
            term_months=term_months,
            monthly_payment=monthly_payment,
            total_interest=total_interest,
            total_repayment=total_repayment,
        )

    @staticmethod
    def calculate_pcp(
        vehicle_price: int,
        deposit: int,
        apr: float,
        term_months: int,
        residual_value: int,
    ) -> FinanceCalculation:
        """
        Calculate Personal Contract Purchase (PCP) finance.
        - Regular monthly payments on depreciation only
        - Finance secured against vehicle
        - Balloon payment or return at end
        """
        # PCP: Only pay off the depreciation
        depreciation = vehicle_price - residual_value
        loan_amount = depreciation - deposit

        if apr == 0:
            monthly_payment = loan_amount / term_months
            total_interest = 0
        else:
            monthly_rate = apr / 12
            numerator = monthly_rate * (1 + monthly_rate) ** term_months
            denominator = (1 + monthly_rate) ** term_months - 1
            monthly_payment = loan_amount * (numerator / denominator)
            total_interest = (monthly_payment * term_months) - loan_amount

        total_repayment = monthly_payment * term_months

        return FinanceCalculation(
            vehicle_price=vehicle_price,
            deposit=deposit,
            loan_amount=loan_amount,
            apr=apr,
            term_months=term_months,
            monthly_payment=monthly_payment,
            total_interest=total_interest,
            total_repayment=total_repayment,
        )

    @staticmethod
    def calculate_personal_loan(
        amount: int,
        apr: float,
        term_months: int,
    ) -> FinanceCalculation:
        """
        Calculate Personal Loan finance.
        - Unsecured loan
        - Can be used for any purpose
        - Regular monthly payments
        """
        loan_amount = amount

        if apr == 0:
            monthly_payment = loan_amount / term_months
            total_interest = 0
        else:
            monthly_rate = apr / 12
            numerator = monthly_rate * (1 + monthly_rate) ** term_months
            denominator = (1 + monthly_rate) ** term_months - 1
            monthly_payment = loan_amount * (numerator / denominator)
            total_interest = (monthly_payment * term_months) - loan_amount

        total_repayment = monthly_payment * term_months

        return FinanceCalculation(
            vehicle_price=amount,
            deposit=0,
            loan_amount=loan_amount,
            apr=apr,
            term_months=term_months,
            monthly_payment=monthly_payment,
            total_interest=total_interest,
            total_repayment=total_repayment,
        )

    @staticmethod
    def compare_finance_options(
        vehicle_price: int,
        deposit: int,
        apr: float,
        term_months: int,
        residual_value: int = None,
    ) -> Dict[str, Any]:
        """
        Compare all finance options for a vehicle.
        Shows HP vs PCP vs Personal Loan side-by-side.
        """
        hp = FinanceCalculator.calculate_hp(vehicle_price, deposit, apr, term_months)

        results = {
            "vehicle_price": vehicle_price,
            "deposit": deposit,
            "term_months": term_months,
            "apr": f"{apr:.2%}",
            "hp": {
                "type": "Hire Purchase",
                "monthly_payment": f"£{hp.monthly_payment:.2f}",
                "total_interest": f"£{hp.total_interest:.2f}",
                "total_repayment": f"£{hp.total_repayment:.2f}",
                "description": "Fixed monthly payments. Own the car at the end.",
            },
            "personal_loan": {
                "type": "Personal Loan",
                "monthly_payment": f"£{hp.monthly_payment:.2f}",
                "total_interest": f"£{hp.total_interest:.2f}",
                "total_repayment": f"£{hp.total_repayment:.2f}",
                "description": "Unsecured loan. Flexible use of funds.",
            },
        }

        # Add PCP if residual value provided
        if residual_value:
            pcp = FinanceCalculator.calculate_pcp(
                vehicle_price, deposit, apr, term_months, residual_value
            )
            results["pcp"] = {
                "type": "Personal Contract Purchase",
                "monthly_payment": f"£{pcp.monthly_payment:.2f}",
                "total_interest": f"£{pcp.total_interest:.2f}",
                "total_repayment": f"£{pcp.total_repayment:.2f}",
                "balloon_payment": f"£{residual_value:.2f}",
                "description": "Pay for depreciation only. Return car at end or pay balloon.",
            }

        return results

    @staticmethod
    def estimate_affordability(
        monthly_budget: int, apr: float, term_months: int, deposit: int = 0
    ) -> Dict[str, Any]:
        """
        Estimate what vehicle price is affordable based on monthly budget.
        This is Zuto's approach - work backwards from monthly payment.
        """
        if apr == 0:
            max_loan = monthly_budget * term_months
        else:
            monthly_rate = apr / 12
            # Rearrange formula to solve for principal
            denominator = (1 + monthly_rate) ** term_months - 1
            numerator = monthly_rate * (1 + monthly_rate) ** term_months
            max_loan = monthly_budget * (denominator / numerator)

        max_vehicle_price = max_loan + deposit

        return {
            "monthly_budget": f"£{monthly_budget:.2f}",
            "deposit": f"£{deposit:.2f}",
            "apr": f"{apr:.2%}",
            "term_months": term_months,
            "max_loan_amount": f"£{max_loan:.2f}",
            "max_vehicle_price": f"£{max_vehicle_price:.2f}",
            "note": "This is a rough estimate. Actual affordability depends on credit check and lender assessment.",
        }
