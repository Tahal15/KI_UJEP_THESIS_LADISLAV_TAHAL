cube(`DimLP`, {
  sql: `SELECT * FROM DimLP`,

  dimensions: {
    LPKey: {
      sql: `toString(LPKey)`,
      primaryKey: true,
      type: `string`,
      title: `Klíč SPZ`
    },

    LicensePlate: {
      sql: `LicensePlate`,
      type: `string`,
      title: `SPZ`
    }
  }
});
