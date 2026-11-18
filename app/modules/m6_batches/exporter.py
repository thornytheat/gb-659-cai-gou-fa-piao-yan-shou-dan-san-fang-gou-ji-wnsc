import csv
import io

def differences_csv(rows: list[dict]) -> str:
    output = io.StringIO(newline="")
    fields = ["business_key", "line_no", "reason_code", "amount_cny"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader(); writer.writerows(rows)
    return output.getvalue()

