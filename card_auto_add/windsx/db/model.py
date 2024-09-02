class FieldValueInvalid(Exception):
    def __init__(self, message: str, field_name: str):
        super().__init__(message)
        self._field_name = field_name

    @property
    def field_name(self) -> str:
        return self._field_name
