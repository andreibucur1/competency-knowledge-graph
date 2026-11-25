//Explorare (o singura data, nu face parte din import)
// LOAD CSV WITH HEADERS FROM 'file:///occupationSkillRelations_en.csv' AS row
// RETURN row.relationType AS tip, count(*) AS cate;


// 1.Reguli  - fara dubluri + campuri obligatorii
CREATE CONSTRAINT occ_uri IF NOT EXISTS FOR (o:Occupation) REQUIRE o.uri IS UNIQUE;

CREATE CONSTRAINT skill_uri IF NOT EXISTS FOR (s:Skill) REQUIRE s.uri IS UNIQUE;

CREATE CONSTRAINT isco_uri IF NOT EXISTS FOR (g:ISCOGroup) REQUIRE g.uri IS UNIQUE;

CREATE INDEX isco_code IF NOT EXISTS FOR (g:ISCOGroup) ON (g.code);

// IS NOT NULL merge doar in Neo4j Enterprise
CREATE CONSTRAINT occ_isco_exists IF NOT EXISTS FOR (o:Occupation) REQUIRE o.iscoGroup IS NOT NULL;



//2.Grupele ISCO

LOAD CSV WITH HEADERS FROM 'file:///ISCOGroups_en.csv' AS row
MERGE (g:ISCOGroup {uri: row.conceptUri})
SET g.code = row.code,
    g.preferredLabel = row.preferredLabel;



//3.Ocupatiile + legatura la grupa ISCO
LOAD CSV WITH HEADERS FROM 'file:///occupations_en.csv' AS row
// doar ocupatiile oficiale (in practica toate sunt 'released', filtrul e de siguranta)
WITH row WHERE row.status = 'released'
MERGE (o:Occupation {uri: row.conceptUri})
SET o.preferredLabel = row.preferredLabel,
    // celulele cu mai multe denumiri (separate prin rand nou) devin liste
    o.altLabels    = [x IN split(coalesce(row.altLabels, ''), '\n') WHERE trim(x) <> '' | trim(x)],
    o.hiddenLabels = [x IN split(coalesce(row.hiddenLabels, ''), '\n') WHERE trim(x) <> '' | trim(x)],
    o.description  = row.description,
    o.scopeNote    = row.scopeNote,
    o.code         = row.code,
    o.iscoGroup    = row.iscoGroup
WITH o, row
MATCH (g:ISCOGroup {code: row.iscoGroup})
MERGE (o)-[:IN_ISCO_GROUP]->(g);



//4.Competentele (pe bucati de cate 1000 de randuri)
:auto
LOAD CSV WITH HEADERS FROM 'file:///skills_en.csv' AS row
WITH row WHERE row.status = 'released'
CALL (row) {
  MERGE (s:Skill {uri: row.conceptUri})
  SET s.preferredLabel = row.preferredLabel,
      s.altLabels    = [x IN split(coalesce(row.altLabels, ''), '\n') WHERE trim(x) <> '' | trim(x)],
      s.hiddenLabels = [x IN split(coalesce(row.hiddenLabels, ''), '\n') WHERE trim(x) <> '' | trim(x)],
      s.description  = row.description,
      s.scopeNote    = row.scopeNote,
      s.definition   = row.definition,
      s.skillType    = row.skillType,
      s.reuseLevel   = row.reuseLevel
} IN TRANSACTIONS OF 1000 ROWS;


//5.Legaturile ocupatie -> competenta (esential/optional)
:auto
LOAD CSV WITH HEADERS FROM 'file:///occupationSkillRelations_en.csv' AS row
CALL (row) {
  MATCH (o:Occupation {uri: row.occupationUri})
  MATCH (s:Skill {uri: row.skillUri})
  FOREACH (_ IN CASE WHEN row.relationType = 'essential' THEN [1] ELSE [] END |
    MERGE (o)-[:REQUIRES_ESSENTIAL {source: 'ESCO v1.2.1'}]->(s))
  FOREACH (_ IN CASE WHEN row.relationType = 'optional' THEN [1] ELSE [] END |
    MERGE (o)-[:REQUIRES_OPTIONAL {source: 'ESCO v1.2.1'}]->(s))
} IN TRANSACTIONS OF 1000 ROWS;


//6.Verificari (rezultate obtinute la importul initial)
// Noduri- ISCOGroup 619, Occupation 3039, Skill 13939
MATCH (n) RETURN labels(n) AS tip, count(*) AS cate;

// Relatii- REQUIRES_ESSENTIAL 67600, REQUIRES_OPTIONAL 58451, IN_ISCO_GROUP 3039
MATCH ()-[r]->() RETURN type(r) AS relatie, count(*) AS cate;

// Ocupatii fara grupa ISCO-total 3039, fara_grupa 0
MATCH (o:Occupation)
RETURN count(o) AS total,
       sum(CASE WHEN NOT EXISTS { (o)-[:IN_ISCO_GROUP]->() } THEN 1 ELSE 0 END) AS fara_grupa;

//Noduri fara uri sau nume-niciun rand
MATCH (n) WHERE n.uri IS NULL OR n.preferredLabel IS NULL
RETURN labels(n) AS tip, count(*) AS cate;

//test: data engineer - 23 esentiale, 5 optionale
MATCH (o:Occupation {preferredLabel: "data engineer"})-[r]->(:Skill)
RETURN type(r) AS relatie, count(*) AS cate;
