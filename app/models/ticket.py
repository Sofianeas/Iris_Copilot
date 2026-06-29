from dataclasses import dataclass, field

from app.models.customer import Customer
from app.models.intervention import Intervention
from app.models.logistics import Logistics
from app.models.procedure import Procedure
from app.models.validation import Validation


@dataclass
class Ticket:

    customer: Customer = field(default_factory=Customer)

    intervention: Intervention = field(default_factory=Intervention)

    logistics: Logistics = field(default_factory=Logistics)

    procedure: Procedure = field(default_factory=Procedure)

    validation: Validation = field(default_factory=Validation)