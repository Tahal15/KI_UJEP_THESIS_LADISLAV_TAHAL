cube(`etl_runlog`, {
  sql_table: `mttgueries.etl_runlog`,
  
  data_source: `default`,
  
  joins: {
    
  },
  
  dimensions: {
    jobname: {
      sql: `${CUBE}.\`JobName\``,
      type: `string`
    },
    
    topic: {
      sql: `${CUBE}.\`Topic\``,
      type: `string`
    },
    
    status: {
      sql: `${CUBE}.\`Status\``,
      type: `string`
    },
    
    errormessage: {
      sql: `${CUBE}.\`ErrorMessage\``,
      type: `string`
    },
    
    starttime: {
      sql: `${CUBE}.\`StartTime\``,
      type: `time`
    },
    
    endtime: {
      sql: `${CUBE}.\`EndTime\``,
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
