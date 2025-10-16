cube(`DimCity`, {
  sql: `SELECT * FROM DimCity`,

  // 🧩 Hlavní dimenze (UUID jako string, protože ClickHouse UUID != number)
  dimensions: {
    CityKey: {
      sql: `toString(CityKey)`,
      primaryKey: true,
      type: `string`,
      title: `Klíč města`
    },

    CityName: {
      sql: `CityName`,
      type: `string`,
      title: `Název města`
    },

    IsActive: {
      sql: `IsActive`,
      type: `boolean`,
      title: `Aktivní záznam`
    }
  }
});
