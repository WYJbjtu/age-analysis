"""Aggregate member-owned source citations without creating shared editing conflicts."""
from pathlib import Path
import csv

ROOT=Path(__file__).resolve().parents[1]
MEMBERS=('member1_demographics','member2_industry','member3_labor_migration')
OUTPUT=ROOT/'docs/source_registry.csv'


def main():
    all_rows=[]
    header=None
    for member in MEMBERS:
        with (ROOT/member/'sources.csv').open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            if header is None:
                header=reader.fieldnames
            elif header != reader.fieldnames:
                raise ValueError(f'{member}: source metadata headers differ')
            for row in reader:
                if any((v or '').strip() for v in row.values()):
                    all_rows.append(row)
    with OUTPUT.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=header)
        writer.writeheader()
        writer.writerows(all_rows)
    print('Source registry:',len(all_rows),'entries ->',OUTPUT)


if __name__=='__main__':
    main()
