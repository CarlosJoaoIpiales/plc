import csv
import os
from datetime import datetime

EXPORT_DIR = "exports/reports"

def export_report_to_csv(serial_number, report_data):
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    filename = f"{EXPORT_DIR}/report_{serial_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Test Type", "Test #", "Initial Reading", "Final Reading", "Error (%)", "Passed", "Date",
            "Brand", "Model", "Diameter", "Batch"
        ])
        for row in report_data:
            writer.writerow([
                row["test_type"],
                row["test_number"],
                row["initial_reading"],
                row["final_reading"],
                f'{row["error"]:.2f}',
                "YES" if row["passed"] else "NO",
                row["test_date"].strftime("%Y-%m-%d %H:%M"),
                row["brand"],
                row["model"],
                row["diameter"],
                row["batch"]
            ])

    return filename
