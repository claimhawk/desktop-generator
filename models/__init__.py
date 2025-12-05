# Copyright (c) 2025 Tylt LLC. All rights reserved.
# Licensed for research use only. Commercial use requires a license from Tylt LLC.
# Contact: hello@claimhawk.app | See LICENSE for terms.

"""Domain models for test_desktop_generator.

Define your data types here (Patient, Provider, Claim, etc.)
with field definitions for realistic data generation.
"""

# Re-export common models for use in this project
from cudag.core import Claim as Claim
from cudag.core import Patient as Patient
from cudag.core import Procedure as Procedure
from cudag.core import Provider as Provider

# Import types for custom model definitions:
# from cudag.core import (
#     Model,
#     StringField,
#     IntField,
#     DateField,
#     ChoiceField,
#     MoneyField,
# )

# Example: Define a custom model
# class MyCustomModel(Model):
#     name = StringField(faker="full_name")
#     account_number = StringField(pattern=r"[A-Z]{2}[0-9]{8}")
#     status = ChoiceField(choices=["Active", "Pending", "Closed"])

__all__ = [
    "Patient",
    "Provider",
    "Procedure",
    "Claim",
]
