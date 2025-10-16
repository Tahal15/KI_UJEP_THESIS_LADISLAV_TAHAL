cube(`DimCity`, {
  sql: `SELECT * FROM dimcity`,

  dimensions: {
    CityKey:  { sql: `CityKey`,  primaryKey: true, type: `number` },
    CityName: { sql: `CityName`, type: `string` },
    IsActive: { sql: `IsActive`, type: `boolean` },
  }
});
