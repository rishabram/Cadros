# Real parcel sample — data sources

Sample built 2026-09-23 (MDT) by `parcel_loader.py` (W2, NERON screen/).
Download date: 2026-09-23.

## 1. Parcel polygons — Utah AGRC "Utah Statewide Parcels"

- Source name: Utah Statewide Parcels (publisher: UtahAGRC)
- Open-data page: https://opendata.gis.utah.gov/datasets/utah::parcels/about
- ArcGIS item: https://www.arcgis.com/home/item.html?id=9df536b0835e4ee78e34d7cf6fe132c2
- REST service (public, no key):
  https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahStatewideParcels/FeatureServer/0
- Layer: `StateWideParcels` (polygon), native SR EPSG:3857 (Web Mercator)
- Full county count at pull time: **398,047 parcels** where County='SaltLake'
  (`.../0/query?where=County='SaltLake'&returnCountOnly=true`)
- Sample pulled: bbox lon −111.95..−111.80, lat 40.72..40.80 (north-central
  Salt Lake City: airport/industrial NW + east-bench residential),
  ordered by OBJECTID, first 1,000 requested; **500 kept** in
  `real_parcels/`.
- Key fields: PARCEL_ID, PARCEL_ADD, PARCEL_CITY, County, Shape__Area.
- License/terms (AGRC): data provided "as is" without warranty of any kind,
  expressed or implied; all quality/performance risk assumed by the user.
  No use restriction beyond the disclaimer; attribute "Utah AGRC".

## 2. Zoning districts — Salt Lake City open data "Zoning"

- Source name: Zoning (publisher: slcgis_slcgov)
- ArcGIS item: https://www.arcgis.com/home/item.html?id=57cf37d10d3b4c1c872828edcaf9bcd2
- REST service (public, no key):
  https://services.arcgis.com/mMBpeYj0vPFotzbe/arcgis/rest/services/zoning/FeatureServer/5
- Layer: `zoning` (polygon), native SR EPSG:3566 ftUS state plane,
  4,852 zone polygons downloaded in full (3 paginated queries).
- District attribution: parcel-centroid-in-zone-polygon; 494/500 by
  containment, 6/500 by nearest-zone fallback (see `district_provenance`
  property — never silent). No join key exists between the two layers;
  the join is purely spatial.
- Key fields: ZONING (e.g. "MU-11"), ZONING_NAME, ZONING_DESC.
- License/terms: listed as "Open Data".

## 3. Reprojection

Both sources reprojected to **EPSG:3566 = NAD83 / Utah Central (ftUS)**,
the canonical "local-feet" planar frame for real Salt Lake County parcels
(`crs: "local-feet"` in every file). A given parcel always maps to the same
coordinates — not a per-parcel arbitrary origin.

Documented geometry transformations (never silent):
- MultiPolygon source shapes → largest part kept.
- Interior rings (holes) → dropped; exterior ring only (W1 screener does
  not handle holes).

## 4. Sample contents (`real_parcels/`)

- 500 files `parcel_<PARCEL_ID>.geojson` (W1-schema: Polygon geometry in
  planar feet; properties `parcel_id`, `crs`, `district`, `zone_label`,
  plus real extras `address`, `city`, `county`, `district_provenance`)
- `parcel_index.geojson` — FeatureCollection of all 500
- District mix: R-1-7000 159, MU-5 137, M-1 59, M-2 38, OS 35, FR-3 21,
  FR-2 20, R-1-5000 13, BP 13, EI 3, RMF-30 1, MU-11 1
- Parcel sizes: 0.00–196.36 ac, median 0.18 ac
- Every parcel is from the real sources above; nothing synthetic is in
  this directory.

## 5. Reproducing / extending

Raw dumps (Esri FeatureSet JSON) were staged in /tmp (ephemeral); to
re-pull:

    # parcels (bbox in 4326, outSR 4326, paginate with resultOffset):
    .../UtahStatewideParcels/FeatureServer/0/query \
      ?where=County='SaltLake'&geometry=<xmin,ymin,xmax,ymax> \
      &geometryType=esriGeometryEnvelope&inSR=4326&outSR=4326 \
      &outFields=PARCEL_ID,PARCEL_ADD,PARCEL_CITY,County,OBJECTID \
      &orderByFields=OBJECTID&resultRecordCount=2000&returnGeometry=true&f=json

    # zoning (full layer, paginate 2000/page):
    .../zoning/FeatureServer/5/query \
      ?where=1=1&outFields=OBJECTID,ZONING,ZONING_NAME \
      &orderByFields=OBJECTID&resultOffset=0&resultRecordCount=2000 \
      &outSR=4326&returnGeometry=true&f=json

    # build sample:
    python parcel_loader.py --source parcels_raw.json --zoning zoning_raw.json \
        --sample 500 --out real_parcels/

County-wide (398k parcels) needs ~200 paginated requests; do that on a
machine with bandwidth, or add a tiling loop over county sub-bboxes.
