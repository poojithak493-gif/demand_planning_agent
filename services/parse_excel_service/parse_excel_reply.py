import pandas as pd


def parse_excel_demand(file_path):
    df = pd.read_excel(file_path)
    return df


if __name__ == "__main__":
    file_path = "attachments/sample_reply.xlsx"
    df = parse_excel_demand(file_path)
    print(df)