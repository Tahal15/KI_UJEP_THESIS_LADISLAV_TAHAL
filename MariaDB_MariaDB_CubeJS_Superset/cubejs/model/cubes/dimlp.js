cube(`DimLP`, {
  sql: `SELECT * FROM dimlp`,

  dimensions: {
    LPKey:        { sql: `LPKey`,        primaryKey: true, type: `number` },
    LicensePlate: { sql: `LicensePlate`, type: `string` },
  }
});
