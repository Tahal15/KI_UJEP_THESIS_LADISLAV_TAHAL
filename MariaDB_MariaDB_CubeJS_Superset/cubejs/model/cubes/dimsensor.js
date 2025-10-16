cube(`DimSensor`, {
  sql: `SELECT * FROM dimsensor`,

  dimensions: {
    SensorKey:  { sql: `SensorKey`,  primaryKey: true, type: `number` },
    SensorCode: { sql: `SensorCode`, type: `string` },
  }
});
