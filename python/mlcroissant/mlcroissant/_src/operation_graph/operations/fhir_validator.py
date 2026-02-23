"""Optional FHIR validation support."""

from typing import Any

from mlcroissant._src.core.optional import deps


class FhirValidator:
    """Optional validator for FHIR resources.

    Validates FHIR resources against HL7 FHIR schemas using fhir.resources.
    Only used when explicitly enabled.
    """

    def __init__(self, validate_fhir: bool = False):
        """Initialize FhirValidator."""
        self.validate_fhir = validate_fhir
        if validate_fhir:
            # Lazy load fhir.resources only when validation enabled
            self._fhir = deps.fhir_resources
        self._resource_classes: dict[str, type] = {}

    def validate_resource(self, resource_dict: dict[str, Any]) -> dict[str, Any]:
        """Validate a FHIR resource dictionary."""
        if not self.validate_fhir:
            return resource_dict

        resource_type = resource_dict.get("resourceType")
        if not resource_type:
            raise ValueError("Missing resourceType in FHIR resource")

        # Get resource class (cached)
        if resource_type not in self._resource_classes:
            module_path = f"fhir.resources.{resource_type.lower()}"
            module = __import__(module_path, fromlist=[resource_type])
            self._resource_classes[resource_type] = getattr(module, resource_type)

        # Validate using Pydantic model
        resource_class = self._resource_classes[resource_type]
        resource_class.model_validate(resource_dict)

        return resource_dict
