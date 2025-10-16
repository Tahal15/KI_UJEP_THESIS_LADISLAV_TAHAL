cube(`DimDetectionType`, {
  sql: `SELECT DetectionTypeKey, DetectionType FROM dimdetectiontype`,

  dimensions: {
    DetectionTypeKey: { sql: `DetectionTypeKey`, primaryKey: true, type: `number` },
    DetectionType:    { sql: `DetectionType`, type: `string` }
  }
});
