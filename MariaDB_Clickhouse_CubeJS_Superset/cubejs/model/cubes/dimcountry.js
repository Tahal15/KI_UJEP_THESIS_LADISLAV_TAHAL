cube(`DimCountry`, {
  sql: `SELECT * FROM DimCountry`,

  dimensions: {
    CountryKey: {
      sql: `toString(CountryKey)`,
      primaryKey: true,
      type: `string`,
      title: `Klíč země`
    },

    CountryCode: {
      sql: `CountryCode`,
      type: `string`,
      title: `Kód země`
    }
  }
});
