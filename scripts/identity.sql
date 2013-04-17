-- ArcGIS-style Unions and Overlays via building new polygons
-- advantage to this method is that you can include polygons from multiple input tables 
-- and overlapping polygons are handled gracefuly by taking the max(id)
--
-- put it all into one table, maintaining ids for each input layer
-- refine query based on active scenario
-- deconstruct into lines and rebuild polygons
-- points on surface
-- group by geom and aggregate original ids by point overlap
-- Replicates an ArcGIS-style Union
-- Join with the original tables to pull in attributes
-- Create an Identity
-- similar to a global arcgis-style union but "clipped" to one of the input layers


-- TODO where clause
-- TODO update trees_spatialconstraints
-- TODO migration
-- TODO variable substitution
-- TODO python wrapper


DROP TABLE IDENTITY;
CREATE TABLE IDENTITY AS


 -- id              | integer                  | not null default nextval('trees_scenariostand_id_seq'::regclass)
 -- user_id         | integer                  | not null
 -- name            | character varying(255)   | not null
 -- date_created    | timestamp with time zone | not null
 -- date_modified   | timestamp with time zone | not null
 -- content_type_id | integer                  |
 -- object_id       | integer                  |
 -- manipulators    | text                     |
 -- cond_id         | bigint                   | not null
 -- rx_id           | integer                  | not null
 -- scenario_id     | integer                  | not null
 -- geometry_orig   | geometry                 |
 -- geometry_final  | geometry                 |


SELECT 1 AS user_id, -- todo var replacement?
       'TEST' AS name, -- todo var replacement?
       NOW() AS date_created,
       NOW() AS date_modified,
       geometry_final,
       cond_id,
       default_rx_id as rx_id, 
       1 AS scenario_id, -- todo var replacement?
       stand_id
       constraint_id

FROM
  (SELECT z.geom AS geometry_final,
          stand_id,
          constraint_id,
          default_rx_id,
          cond_id
   FROM
     (SELECT new.geom AS geom,
             Max(orig.stand_id) AS stand_id,
             Max(orig.constraint_id) AS constraint_id
      FROM
        (SELECT id AS stand_id,
                NULL AS constraint_id,
                geometry_final AS geom
         FROM trees_stand
         UNION ALL SELECT NULL AS stand_id,
                          id AS constraint_id,
                          geom
         FROM trees_spatialconstraint) AS orig,

        (SELECT St_pointonsurface(geom) AS geom
         FROM
           (SELECT geom
            FROM St_dump(
                           (SELECT St_polygonize(the_geom) AS the_geom
                            FROM
                              (SELECT St_union(the_geom ) AS the_geom
                               FROM
                                 (SELECT St_exteriorring( geom) AS the_geom
                                  FROM
                                    (SELECT id AS stand_id, NULL AS constraint_id, geometry_final AS geom
                                     FROM trees_stand
                                     -- WHERE user_id = ___ AND id IN (....)
                                     UNION ALL SELECT NULL AS stand_id , id AS constraint_id, geom
                                     FROM trees_spatialconstraint
                                     -- WHERE category in () AND bbox overlaps property
                                     ) AS _test2_combo ) AS lines) AS noded_lines))) AS _test2_overlay) AS pt,

        (SELECT geom
         FROM St_dump(
                        (SELECT St_polygonize(the_geom) AS the_geom
                         FROM
                           (SELECT St_union(the_geom) AS the_geom
                            FROM
                              (SELECT St_exteriorring(geom) AS the_geom
                               FROM
                                 (SELECT id AS stand_id, NULL AS constraint_id, geometry_final AS geom
                                  FROM trees_stand
                                  -- WHERE user_id = ___ AND id IN (....)
                                  UNION ALL SELECT NULL AS stand_id, id AS constraint_id, geom
                                  FROM trees_spatialconstraint
                                  -- WHERE category in () AND bbox overlaps property
                                  ) AS _test2_combo ) AS lines) AS noded_lines))) AS new
      WHERE orig.geom && pt.geom
        AND new.geom && pt.geom
        AND Intersects(orig.geom, pt.geom)
        AND Intersects(new.geom, pt.geom)
      GROUP BY new.geom) AS z
   LEFT JOIN trees_stand s ON s.id = z.stand_id
   LEFT JOIN trees_spatialconstraint c ON c.id = z.constraint_id) AS _test2_unionjoin
WHERE stand_id IS NOT NULL ;