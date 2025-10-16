cube(`DimDetectionType`, {
  sql: `SELECT * FROM DimDetectionType`,

  dimensions: {
    DetectionTypeKey: {
      sql: `toString(DetectionTypeKey)`,
      primaryKey: true,
      type: `string`,
      title: `Klíč typu detekce`
    },

    DetectionType: {
      sql: `DetectionType`,
      type: `string`,
      title: `Typ detekce`
    }
  }
});
