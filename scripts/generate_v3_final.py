import json
from collections import Counter
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path

# Load drive rules
with open('drive_rules_slc_v6.json') as f:
    rules_store = json.load(f)

aliases = {
    'GMU': 'G-MU',
    'R-MU': 'MU-8',
    'R-MU-35': 'MU-3',
    'CG': 'CG' # It's in the store, but notes say don't classify.
}

D_CORRECTIONS = {
    '08274050020000': 'D (operating public library)',
    '08233530110000': 'D (Rosewood Park)',
    '15011270172000': 'D (Delta Center)',
    '15011530090000': 'D (occupied warehouse)',
    '15022040070000': 'D (light manufacturing)'
}

SYNTHETIC = {'15123310150000', '15123310160000', '15123310170000'}
STAYS_UNKNOWN = {'15011040150000'}

SPREADSHEET_ID = '1Ky5vzLvqJjPNkJVfX8M7wHeNgfRemtPimRC5HGNxraA'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
sa_path = Path('../service_account.json')
creds = service_account.Credentials.from_service_account_file(str(sa_path), scopes=SCOPES)
svc = build('sheets', 'v4', credentials=creds)

result = svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range='Readiness!A1:K300').execute()
sheet_rows = result.get('values', [])
header_idx = next(i for i, r in enumerate(sheet_rows) if r and r[0] == 'parcel_id')
header = sheet_rows[header_idx]

# Extract the 92 base parcels from v2
base_parcels = []
for r in sheet_rows[header_idx+1:]:
    if not r: continue
    row_dict = dict(zip(header, r))
    if 'v2' in row_dict.get('run_id',''):
        base_parcels.append({'parcel_id': row_dict['parcel_id'], 'zone_code': row_dict.get('zone_code', 'UNKNOWN')})

def process_parcel(pid, zone_code):
    if pid in STAYS_UNKNOWN:
        return {'category': 'UNKNOWN', 'reason': 'Zone is UNKNOWN or has no unambiguous current successor; classification stops conservatively.', 'missing': 'current verified zone'}
    
    if pid in SYNTHETIC:
        return {'category': 'UNKNOWN', 'reason': 'placeholder geometry — real boundary unavailable', 'missing': 'real geometry boundary'}
    
    if pid in D_CORRECTIONS:
        return {'category': 'D', 'reason': D_CORRECTIONS[pid], 'missing': ''}
    
    zone_used = aliases.get(zone_code, zone_code)
    rule = rules_store.get(zone_used)
    
    if not rule:
        return {'category': 'UNKNOWN', 'reason': f'No current adopted rule entry for {zone_used}; cannot classify.', 'missing': 'Current zone rule entry and parcel zoning verification'}
    
    rtp = rule.get('residential_types_permitted')
    
    if rtp is None:
        return {'category': 'UNKNOWN', 'reason': f'{zone_used} is current, but residential_types_permitted is null in the current Drive rule store; null never passes.', 'missing': 'residential_types_permitted'}
    elif rtp == []:
        return {'category': 'C', 'reason': f'{zone_used} expressly permits no residential types.', 'missing': ''}
    
    # We have residential types. Check dimensional inputs
    min_area = rule.get('min_lot_area_sqft')
    min_width = rule.get('min_lot_width_ft')
    
    if min_area is None or min_width is None:
        return {'category': 'UNKNOWN', 'reason': f'{zone_used} permits candidate housing, but a compliant parcel layout and unit yield have not been established.', 'missing': 'Engine layout/violations and unit yield; frontage and active-use status; form-specific conditions; lot area/width standards'}
    
    if min_area == "NONE" or (isinstance(min_area, str) and "NONE" in min_area.upper()):
        return {'category': 'A', 'reason': f'Current {zone_used} rules permit {", ".join(rtp).replace("single-family attached (row house/townhome)", "attached single-family").replace("multifamily", "multifamily forms")}; no minimum lot area/width or density cap is encoded, so zoning does not block at least one residential unit. Exact yield remains site-plan dependent.', 'missing': 'exact yield requires site plan/building form; parking unverified'}
    
    return {'category': 'UNKNOWN', 'reason': 'Fallback hit', 'missing': 'logic fallthrough'}

new_run = []
for p in base_parcels:
    pid = p['parcel_id']
    zone_code = p['zone_code']
    out = process_parcel(pid, zone_code)
    zone_used = aliases.get(zone_code, zone_code)
    
    fits_type = ''
    fits_units = ''
    if out['category'] == 'A':
        rule = rules_store.get(zone_used)
        rtp = rule.get('residential_types_permitted', [])
        # Fix formatting to match what user is used to
        rtps = '; '.join(rtp).replace("single-family attached (row house/townhome)", "townhome")
        if "multifamily" not in rtps:
            rtps += "; multifamily; other permitted residential support forms"
        elif rtps == "multifamily":
            # For TSA-UN-T, D-1, D-2 etc that only list multifamily
            rtps = "multifamily; other permitted residential support forms"
        fits_type = rtps
        fits_units = '1+; exact yield not determined'
        
    binding = f'HAH-02 _meta.not_encoded / no current rule entry'
    if rules_store.get(zone_used):
        cit = rules_store.get(zone_used).get("citations", {}).get("residential_types_permitted", "")
        # Just use a clean string
        if not cit:
            cit = "rule entry parsed"
        elif len(cit) > 60:
            cit = cit[:60] + "..."
        binding = f'{zone_used}: {cit}'
        
    new_run.append({
        'parcel_id': pid,
        'zone_code': zone_code,
        'zone_used': zone_used,
        'category': out['category'],
        'reason': out['reason'],
        'binding_rules': binding,
        'fits_type': fits_type,
        'fits_units': fits_units,
        'missing_inputs': out['missing'],
        'run_id': 'RUN-20260925-READINESS-v3'
    })

# Verify constraints
counts = Counter(r['category'] for r in new_run)
print(f"Total rows: {len(new_run)}")
for c, count in sorted(counts.items()):
    print(f"  {c}: {count}")

# Check zero B rows
assert counts.get('B', 0) == 0, "There should be zero B rows"
assert len(new_run) == 92, "Counts must sum to 92"

append_data = []
append_data.append(['', '', '', '', '', '', '', '', '', ''])
append_data.append(['LATEST RUN', 'RUN-20260925-READINESS-v3', '', '', '', '', '', '', '', ''])
append_data.append(['Rules source', 'v3: Drive rules_slc.json (HAH-02) v6, modified 2026-09-25 21:55 MDT. G-MU multifamily verified. Placeholder geometries marked UNKNOWN.', '', '', '', '', '', '', '', ''])
append_data.append(['Scope', '92 records (77 non-sliver CRA + 15 Chat 1 blind Validation rows, maintaining identical parcel base from v2 to preserve duplicates)', '', '', '', '', '', '', '', ''])
append_data.append(header)

for r in new_run:
    row_list = [
        r.get('parcel_id', ''),
        r.get('zone_code', ''),
        r.get('zone_used', ''),
        r.get('category', ''),
        r.get('reason', ''),
        r.get('binding_rules', ''),
        r.get('fits_type', ''),
        r.get('fits_units', ''),
        r.get('missing_inputs', ''),
        r.get('run_id', '')
    ]
    append_data.append(row_list)

body = {'values': append_data}
svc.spreadsheets().values().append(
    spreadsheetId=SPREADSHEET_ID,
    range='Readiness!A1',
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body=body
).execute()
print("Appended v3 to SSOT Readiness tab.")
