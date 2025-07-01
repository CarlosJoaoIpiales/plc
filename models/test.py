class Test:
    def __init__(self, meter_id, test_type, test_number, initial, final, reference=100):
        self.meter_id = meter_id
        self.test_type = test_type
        self.test_number = test_number
        self.initial_reading = initial
        self.final_reading = final
        self.reference_value = reference
        self.error = ((final - initial - reference) / reference) * 100
        self.passed = abs(self.error) <= 2  # will depend on batch in future
