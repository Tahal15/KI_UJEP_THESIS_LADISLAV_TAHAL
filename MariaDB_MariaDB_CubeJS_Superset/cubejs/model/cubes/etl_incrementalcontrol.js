cube(`etl_incrementalcontrol`, {
  sql_table: `mttgueries.etl_incrementalcontrol`,
  
  data_source: `default`,
  
  joins: {
    
  },
  
  dimensions: {
    topic: {
      sql: `${CUBE}.\`Topic\``,
      type: `string`
    },
    
    lastupdate: {
      sql: `${CUBE}.\`LastUpdate\``,
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
