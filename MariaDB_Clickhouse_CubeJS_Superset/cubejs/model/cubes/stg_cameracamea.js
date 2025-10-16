cube(`stg_cameracamea`, {
  sql_table: `mttgueries.stg_cameracamea`,
  
  data_source: `default`,
  
  joins: {
    
  },
  
  dimensions: {
    city: {
      sql: `${CUBE}.\`City\``,
      type: `string`
    },
    
    detectiontype: {
      sql: `${CUBE}.\`DetectionType\``,
      type: `string`
    },
    
    lp: {
      sql: `${CUBE}.\`LP\``,
      type: `string`
    },
    
    sensor: {
      sql: `${CUBE}.\`Sensor\``,
      type: `string`
    },
    
    ilpc: {
      sql: `${CUBE}.\`ILPC\``,
      type: `string`
    },
    
    loaddttm: {
      sql: `${CUBE}.\`LoadDttm\``,
      type: `time`
    },
    
    originaltime: {
      sql: `${CUBE}.\`OriginalTime\``,
      type: `time`
    },
    
    utc: {
      sql: `${CUBE}.\`Utc\``,
      type: `time`
    }
  },
  
  measures: {
    count: {
      type: `count`
    }
  },
  
  pre_aggregations: {
    // Pre-aggregation definitions go here.
    // Learn more in the documentation: https://cube.dev/docs/caching/pre-aggregations/getting-started
  }
});
