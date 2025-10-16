cube(`DimCountry`, {
  sql: `SELECT * FROM dimcountry`,

  dimensions: {
    CountryKey:  { sql: `CountryKey`,  primaryKey: true, type: `number` },
    CountryCode: { sql: `CountryCode`, type: `string` },
  }
});
