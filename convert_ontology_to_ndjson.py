import argparse
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    df = (pd
        .read_csv(args.input, usecols=["ontology", "unit", "units", "description"])
        .rename({
            "ontology": "name",
            "unit": "type",
        }, axis="columns")
        .fillna("")
        .sort_values(["name"])
        .to_json(args.output, lines=True, orient="records")
    )


if __name__ == "__main__":
    main()
