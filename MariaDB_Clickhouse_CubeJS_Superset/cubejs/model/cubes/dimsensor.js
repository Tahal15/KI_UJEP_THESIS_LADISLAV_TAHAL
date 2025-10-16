cube(`DimSensor`, {
  sql: `SELECT * FROM DimSensor`,

  dimensions: {
    SensorKey: {
      sql: `toString(SensorKey)`,
      primaryKey: true,
      type: `string`,
      title: `Klíč senzoru`
    },

    SensorCode: {
      sql: `SensorCode`,
      type: `string`,
      title: `Kód senzoru`
    }
  }
});
