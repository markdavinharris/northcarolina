import sys
Y, ABEV, VF, ED = {'2026':('2026','abev_2026','voters','2026-11-03'),'2024':('2024','abev_2024','voterfile_2024','2024-11-05'),'2022':('2022','abev_2022','voterfile_2022','2022-11-08')}[sys.argv[1]]
chunk = sys.argv[2]
print(f"""WITH a AS (
  SELECT IFNULL(REGEXP_REPLACE(UPPER(a.Jurisname), ' COUNTY$', ''), 'UNKNOWN') AS county,
    a.RequestDate, a.ReturnDate, a.EarlyVoted, a.Rejected,
    CASE WHEN v.PartyRollUp IN ('Republican','Modeled Republican') THEN 'R' WHEN v.PartyRollUp IN ('Democrat','Modeled Democrat') THEN 'D' ELSE 'O' END AS party
  FROM `coldspark-voterdata.national_file.{ABEV}` a
  LEFT JOIN `coldspark-voterdata.national_file.{VF}` v ON v.DT_Regid = a.DT_Regid AND v.State = 'NC'
  WHERE a.State = 'NC'
),
u AS (
  SELECT county, 'req' AS m, DATE_DIFF(DATE '{ED}', RequestDate, DAY) AS d, party FROM a WHERE Rejected = 0 AND RequestDate BETWEEN DATE '{Y}-01-01' AND DATE '{Y}-12-31'
  UNION ALL SELECT county, 'ret', DATE_DIFF(DATE '{ED}', ReturnDate, DAY), party FROM a WHERE Rejected = 0 AND ReturnDate BETWEEN DATE '{Y}-01-01' AND DATE '{Y}-12-31'
  UNION ALL SELECT county, 'eip', DATE_DIFF(DATE '{ED}', EarlyVoted, DAY), party FROM a WHERE EarlyVoted BETWEEN DATE '{Y}-01-01' AND DATE '{Y}-12-31'
)
SELECT county, d,
  COUNTIF(m='req' AND party='R') reqR, COUNTIF(m='req' AND party='D') reqD, COUNTIF(m='req' AND party='O') reqO,
  COUNTIF(m='ret' AND party='R') retR, COUNTIF(m='ret' AND party='D') retD, COUNTIF(m='ret' AND party='O') retO,
  COUNTIF(m='eip' AND party='R') eipR, COUNTIF(m='eip' AND party='D') eipD, COUNTIF(m='eip' AND party='O') eipO,
  REPEAT('x',300) pad
FROM u WHERE d BETWEEN -14 AND 60 AND {chunk} GROUP BY county, d ORDER BY county, d""")
